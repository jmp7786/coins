import smtplib
import os
from email.mime.text import MIMEText

from configs.common import conf

dir_path = os.path.dirname(os.path.realpath(__file__))

# 보낼 메시지 설정
# 메일 보내기
class Notice:
        def __init__(self):
                self.mailer_count = 0
        def get_mail_list(self, level):
                _list = list()
                try:
                        for i in level:
                                if (str(i) in conf['mail']['level']):
                                        _list += conf['mail']['level'][str(i)]
                except TypeError:
                        if (str(level) in conf['mail']['level']):
                                _list += conf['mail']['level'][str(level)]
                
               
                 
                print(_list)
                return _list

        def get_mailer(self):
                _list = conf['mail']['mailer']
        
                if self.mailer_count + 1 > len(_list):
                        self.mailer_count = 0
        
                result = _list[self.mailer_count]
        
                self.mailer_count += 1
        
                return result
                
        def _send_mail(self,sub,msg, receive_mail):
                mailer = self.get_mailer()
                # 세션 생성
                s = smtplib.SMTP('smtp.gmail.com', 587)
                # TLS 보안 시작
                s.starttls()
                # 로그인 인증
                s.login(mailer['id'], mailer['pw'])
                
                msg = MIMEText(msg)
                msg['Subject'] = sub
                
                s.sendmail(mailer['id'], receive_mail, msg.as_string())
            
        def notice(self, sub, msg, level):
                
                mail_list = self.get_mail_list(level)
                for i in mail_list:
                        self._send_mail(sub, msg, i)
                
               # s.sendmail("macicanto@gmail.com", "gotoilhwan@naver.com", msg.as_string())
        
if __name__ == "__main__":
        notice = Notice()
        notice.notice("1","1","1")

