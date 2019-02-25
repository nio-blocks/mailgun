from nio import Block
from nio.block.mixins import EnrichSignals
from nio.properties import VersionProperty, PropertyHolder, StringProperty, ObjectProperty, ListProperty, BoolProperty, Property
from fluentmail.backends import Mailgun as MailgunBackend
from fluentmail import Message as FluentMessage

class MailgunCreds(PropertyHolder):
    api_domain = Property(title="Domain", default="[[MAILGUN_DOMAIN]]")
    api_key = Property(title="API Key", default="[[MAILGUN_API_KEY]]")

class Recipient(PropertyHolder):
    recip = StringProperty(title=" ", default="{{ $email }}")

class Emails(PropertyHolder):
    sender = StringProperty(title="From", default="<no-reply@mydomain.com>", order=1)
    to_recipients = ListProperty(Recipient, title="To", default=[], order=2)
    cc_recipients = ListProperty(Recipient, title="CC", default=[], order=3)
    bcc_recipients = ListProperty(Recipient, title="BCC", default=[], order=4)

class Message(PropertyHolder):
    subject = StringProperty(title="Subject", default="Subject")
    text = StringProperty(title="Plain Text", default="Message text")
    html = StringProperty(title="HTML", default="<b>Message HTML</b>")

class MailGun(EnrichSignals, Block):

    version = VersionProperty('0.1.0')
    creds = ObjectProperty(MailgunCreds, title="API Credentials", order=0)
    emails = ObjectProperty(Emails, title="From / To / CC / BCC", order=1)
    message = ObjectProperty(Message, title="Message", order=2)

    def process_signal(self, signal, input_id=None):
        _api_domain = self.creds().api_domain(signal)
        _api_key = self.creds().api_key(signal)
        _text = self.message().text(signal)
        _html = self.message().html(signal)
        _subject = self.message().subject(signal)
        _sender = self.emails().sender(signal)
        _to_recipients = []
        _cc_recipients = []
        _bcc_recipients = []

        for recipient in self.emails().to_recipients():
            _to_recipients.append(recipient.recip(signal))

        for recipient in self.emails().cc_recipients():
            _cc_recipients.append(recipient.recip(signal))

        for recipient in self.emails().bcc_recipients():
            _bcc_recipients.append(recipient.recip(signal))

        try:
            with MailgunBackend(_api_domain, _api_key) as backend:
                msg = FluentMessage(_subject, _text, 
                    html=_html, 
                    from_address=_sender, 
                    to=_to_recipients, 
                    cc=_cc_recipients, 
                    bcc=_bcc_recipients          
                    )
                msg.send(backend)

            self.notify_signals(self.get_output_signal({'error': 0, 'message': 'Password reset email sent.' }, signal))

        except Exception as e:
            self.notify_signals(self.get_output_signal({'error': 1, 'message': e.args[0] }, signal))
                