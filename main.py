import sys
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from clock.puncher import Puncher
from clock.holiday_checker import HolidayChecker
from clock.holiday_guard import run_with_holiday_check
from clock.scheduler import schedule_today_jobs
# from check_net_itpg.network import ensure_network

# ----------- 初始化--------------
puncher = Puncher(
    config_path=r"C:\Users\user\source\repos\AutoClock\config\config.json",
    model_path=r"C:\Users\user\source\repos\AutoClock\captcha\captcha_model.h5",
    dataset_path=r"C:\Users\user\source\repos\AutoClock\captcha_dataset"
)

checker = HolidayChecker(
    credentials_json="config/credentials.json",
    sheet_id="1Djkq8akgmFrBOxnhntJS3JdT5QZFPh5rfii1xzXrBMo"
)

scheduler = BlockingScheduler()

# network = NetworkManager(config_path=r"C:\Users\user\source\repos\AutoClock\config\itp_guest.json")

# --------- 主程式---------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python main.py [signin|signout|schedule]")
        sys.exit(1)

    command = sys.argv[1].lower()

    # 執行任何打卡動作前，先檢查網路
    # if not network.ensure_network():
    #     print("網路連線或登入失敗，無法繼續")
    #     sys.exit(1)

    if command == "signin":
        run_with_holiday_check("上班打卡", puncher.sign_in, checker)

    elif command == "signout":
        run_with_holiday_check("下班打卡", puncher.sign_out, checker)

    elif command == "schedule":
        # 啟動時先排今天的打卡
        schedule_today_jobs(puncher, checker, scheduler)

        # 每天凌晨 00:01 排當天打卡（週一到週五）
        scheduler.add_job(
            lambda: schedule_today_jobs(puncher, checker, scheduler),
            CronTrigger(hour=0, minute=1, day_of_week="mon-fri")
        )

        print("排程啟動中…")
        scheduler.start()

    else:
        print("未知命令")
