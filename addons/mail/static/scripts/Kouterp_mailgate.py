#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.
"""
    Kouterp_mailgate.py
"""

import cgitb
import time
import optparse
import sys
try:
    from xmlrpc import client as xmlrpclib
except ImportError:
    import xmlrpclib
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import Encoders

class DefaultConfig(object):
    """
    Default configuration
    """
    KOUTERP_DEFAULT_USER_ID = 1
    KOUTERP_DEFAULT_PASSWORD = 'admin'
    KOUTERP_HOSTNAME = 'localhost'
    KOUTERP_PORT = 7073
    KOUTERP_DEFAULT_DATABASE = 'Kouterp'
    MAIL_ERROR = 'error@example.com'
    MAIL_SERVER = 'smtp.example.com'
    MAIL_SERVER_PORT = 25
    MAIL_ADMINS = ('info@example.com',)

config = DefaultConfig()


def send_mail(_from_, to_, subject, text, files=None, server=config.MAIL_SERVER, port=config.MAIL_SERVER_PORT):
    assert isinstance(to_, (list, tuple))

    if files is None:
        files = []

    msg = MIMEMultipart()
    msg['From'] = _from_
    msg['To'] = COMMASPACE.join(to_)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach( MIMEText(text) )

    for file_name, file_content in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload( file_content )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"'
                       % file_name)
        msg.attach(part)

    smtp = smtplib.SMTP(server, port=port)
    smtp.sendmail(_from_, to_, msg.as_string() )
    smtp.close()

class RPCProxy(object):
    def __init__(self, uid, passwd,
                 host=config.KOUTERP_HOSTNAME,
                 port=config.KOUTERP_PORT,
                 path='object',
                 dbname=config.KOUTERP_DEFAULT_DATABASE):
        self.rpc = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/%s' % (host, port, path), allow_none=True)
        self.user_id = uid
        self.passwd = passwd
        self.dbname = dbname

    def __call__(self, *request, **kwargs):
        return self.rpc.execute(self.dbname, self.user_id, self.passwd, *request, **kwargs)

class EmailParser(object):
    def __init__(self, uid, password, dbname, host, port, model=False, email_default=False):
        self.rpc = RPCProxy(uid, password, host=host, port=port, dbname=dbname)
        if model:
            try:
                self.model_id = int(model)
                self.model = str(model)
            except:
                self.model_id = self.rpc('ir.model', 'search', [('model', '=', model)])[0]
                self.model = str(model)
            self.email_default = email_default


    def parse(self, message, custom_values=None, save_original=None):
        # pass message as bytes because we don't know its encoding until we parse its headers
        # and hence can't convert it to utf-8 for transport
        return self.rpc('mail.thread',
                        'message_process',
                        self.model,
                        xmlrpclib.Binary(message),
                        custom_values or {},
                        save_original or False)

def configure_parser():
    parser = optparse.OptionParser(usage='usage: %prog [options]', version='%prog v1.1')
    group = optparse.OptionGroup(parser, "Note",
        "This program parse a mail from standard input and communicate "
        "with the Flectra server for case management in the CRM module.")
    parser.add_option_group(group)
    parser.add_option("-u", "--user", dest="userid",
                      help="Flectra user id to connect with",
                      default=config.KOUTERP_DEFAULT_USER_ID, type='int')
    parser.add_option("-p", "--password", dest="password",
                      help="Flectra user password",
                      default=config.KOUTERP_DEFAULT_PASSWORD)
    parser.add_option("-o", "--model", dest="model",
                      help="Name or ID of destination model",
                      default="crm.lead")
    parser.add_option("-m", "--default", dest="default",
                      help="Admin email for error notifications.",
                      default=None)
    parser.add_option("-d", "--dbname", dest="dbname",
                      help="Flectra database name (default: %default)",
                      default=config.KOUTERP_DEFAULT_DATABASE)
    parser.add_option("--host", dest="host",
                      help="Flectra Server hostname",
                      default=config.KOUTERP_HOSTNAME)
    parser.add_option("--port", dest="port",
                      help="Flectra Server XML-RPC port number",
                      default=config.KOUTERP_PORT)
    parser.add_option("--custom-values", dest="custom_values",
                      help="Dictionary of extra values to pass when creating records",
                      default=None)
    parser.add_option("-s", dest="save_original",
                      action="store_true",
                      help="Keep a full copy of the email source attached to each message",
                      default=False)

    return parser

def main():
    """
    Receive the email via the stdin and send it to the Flectra Server
    """

    parser = configure_parser()
    (options, args) = parser.parse_args()
    email_parser = EmailParser(options.userid,
                               options.password,
                               options.dbname,
                               options.host,
                               options.port,
                               model=options.model,
                               email_default= options.default)
    msg_txt = sys.stdin.read()
    custom_values = {}
    try:
        custom_values = dict(eval(options.custom_values or "{}" ))
    except:
        import traceback
        traceback.print_exc()

    try:
        email_parser.parse(msg_txt, custom_values, options.save_original or False)
    except Exception:
        msg = '\n'.join([
            'parameters',
            '==========',
            '%r' % (options,),
            'traceback',
            '=========',
            '%s' % (cgitb.text(sys.exc_info())),
        ])

        subject = '[Flectra]:ERROR: Mailgateway - %s' % time.strftime('%Y-%m-%d %H:%M:%S')
        send_mail(
            config.MAIL_ERROR,
            config.MAIL_ADMINS,
            subject, msg, files=[('message.txt', msg_txt)]
        )
        sys.stderr.write("Failed to deliver email to Flectra Server, sending error notification to %s\n" % config.MAIL_ADMINS)

if __name__ == '__main__':
    main()
