from login.login import CookiesGenerate
from accounts.importer import Import
from cookiespool.scheduler import Scheduler
from cookiespool.tester import XueqiuValidTester



def main():
    s = Scheduler()
    s.run()

    # 调试用以下代码
    #username = '18987138002'
    #password = 'px758975'
    #l = CookiesGenerate(username,password)
    #cookie = l.main()

if __name__ == '__main__':
    main()
