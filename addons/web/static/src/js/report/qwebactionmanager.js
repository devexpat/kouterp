flectra.define('report.report', function (require) {
'use strict';

var ActionManager = require('web.ActionManager');
var core = require('web.core');
var crash_manager = require('web.crash_manager');
var framework = require('web.framework');

var _t = core._t;
var _lt = core._lt;


var wkhtmltopdf_state;

// Messages that will be shown to the user (if needed).
var WKHTMLTOPDF_MESSAGES = {
    'install': _lt('Unable to find Wkhtmltopdf on this \nsystem. The report will be shown in html.<br><br><a href="http://wkhtmltopdf.org/" target="_blank">\nwkhtmltopdf.org</a>'),
    'workers': _lt('You need to start Kouterp with at least two \nworkers to print a pdf version of the reports.'),
    'upgrade': _lt('You should upgrade your version of\nWkhtmltopdf to at least 0.12.0 in order to get a correct display of headers and footers as well as\nsupport for table-breaking between pages.<br><br><a href="http://wkhtmltopdf.org/" \ntarget="_blank">wkhtmltopdf.org</a>'),
    'broken': _lt('Your installation of Wkhtmltopdf seems to be broken. The report will be shown in html.<br><br><a href="http://wkhtmltopdf.org/" target="_blank">wkhtmltopdf.org</a>')
};

var trigger_download = function (session, response, c, action, options) {
    return session.get_file({
        url: '/report/download',
        data: {data: JSON.stringify(response)},
        complete: framework.unblockUI,
        error: c.rpc_error.bind(c),
        success: function () {
            if (action && options && !action.dialog) {
                options.on_close();
            }
        },
    });
};

/**
 * This helper will generate an object containing the report's url (as value)
 * for every qweb-type we support (as key). It's convenient because we may want
 * to use another report's type at some point (for example, when `qweb-pdf` is
 * not available).
 */
var make_report_url = function (action) {
    var report_urls = {
        'qweb-html': '/report/html/' + action.report_name,
        'qweb-pdf': '/report/pdf/' + action.report_name,
    };
    // We may have to build a query string with `action.data`. It's the place
    // were report's using a wizard to customize the output traditionally put
    // their options.
    if (_.isUndefined(action.data) || _.isNull(action.data) || (_.isObject(action.data) && _.isEmpty(action.data))) {
        if (action.context.active_ids) {
            var active_ids_path = '/' + action.context.active_ids.join(',');
            // Update the report's type - report's url mapping.
            report_urls = _.mapObject(report_urls, function (value, key) {
                return value += active_ids_path;
            });
        }
    } else {
        var serialized_options_path = '?options=' + encodeURIComponent(JSON.stringify(action.data));
        serialized_options_path += '&context=' + encodeURIComponent(JSON.stringify(action.context));
        // Update the report's type - report's url mapping.
        report_urls = _.mapObject(report_urls, function (value, key) {
            return value += serialized_options_path;
        });
    }
    return report_urls;
};

ActionManager.include({
    ir_actions_report: function (action, options) {
        var self = this;
        action = _.clone(action);

        var report_urls = make_report_url(action);

        if (action.report_type === 'qweb-html') {
            var client_action_options = _.extend({}, options, {
                report_url: report_urls['qweb-html'],
                report_name: action.report_name,
                report_file: action.report_file,
                data: action.data,
                context: action.context,
                name: action.name,
                display_name: action.display_name,
            });
            return this.do_action('report.client_action', client_action_options);
        } else if (action.report_type === 'qweb-pdf') {
            framework.blockUI();
            // Before doing anything, we check the state of wkhtmltopdf on the server.
            (wkhtmltopdf_state = wkhtmltopdf_state || this._rpc({route: '/report/check_wkhtmltopdf'})).then(function (state) {
                // Display a notification to the user according to wkhtmltopdf's state.
                if (WKHTMLTOPDF_MESSAGES[state]) {
                    self.do_notify(_t('Report'), WKHTMLTOPDF_MESSAGES[state], true);
                }

                if (state === 'upgrade' || state === 'ok') {
                    // Trigger the download of the PDF report.
                    var response;
                    var c = crash_manager;

                    var treated_actions = [];
                    var current_action = action;
                    do {
                        report_urls = make_report_url(current_action);
                        response = [
                            report_urls['qweb-pdf'],
                            action.report_type, //The 'root' report is considered the maine one, so we use its type for all the others.
                        ];
                        var success = trigger_download(self.getSession(), response, c, current_action, options);
                        if (!success) {
                            self.do_warn(_t('Warning'), _t('A popup window with your report was blocked.  You may need to change your browser settings to allow popup windows for this page.'), true);
                        }

                        treated_actions.push(current_action);
                        current_action = current_action.next_report_to_generate;
                    } while (current_action && !_.contains(treated_actions, current_action));
                    //Second part of the condition for security reasons (avoids infinite loop possibilty).

                    return;

                } else {
                    // Open the report in the client action if generating the PDF is not possible.
                    var client_action_options = _.extend({}, options, {
                        report_url: report_urls['qweb-html'],
                        report_name: action.report_name,
                        report_file: action.report_file,
                        data: action.data,
                        context: action.context,
                        name: action.name,
                        display_name: action.display_name,
                    });
                    framework.unblockUI();
                    return self.do_action('report.client_action', client_action_options);
                }
            });
        } else {
            self.do_warn(_t('Error'), _t('Non qweb reports are not anymore supported.'), true);
            return;
        }
    }
});

});
