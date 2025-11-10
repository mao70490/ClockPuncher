import sys, os, asyncio, ctypes
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from clock.puncher import Puncher
from clock.holiday_checker import HolidayChecker
from clock.holiday_guard import run_with_holiday_check
from clock.scheduler import schedule_today_jobs
from check_net_itpg.network import NetworkManager

# ----------- 網路先初始化--------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

network = NetworkManager(
    config_path=os.path.join(BASE_DIR, "config", "itp_guest.json")
)

# --------- 主程式---------------
if __name__ == "__main__":
    # -------- 防止系統進入睡眠 --------
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)

    try:
        if len(sys.argv) < 2:
            print("用法: python main.py [signin|signout|schedule]")
            sys.exit(1)

        command = sys.argv[1].lower()

        # -------- 網路登入測試 ----------
        if command == "network":
            success, msg = network.ensure_network()
            print(f"網路登入測試結果: {msg}")
            if success:
                print("網路登入成功 ✅")
            else:
                print("網路登入失敗 ❌")
            sys.exit(0)

        # -------- 執行任何打卡前先檢查網路 ----------
        success, net_msg = network.ensure_network()
        print(f"啟動專案後網路檢查結果: {net_msg}")
        if not success:
            print("網路連線或登入失敗，無法繼續")
            sys.exit(1)

        # -------- 網路檢查成功後再初始化其他物件 ----------
        puncher = Puncher(
            config_path=os.path.join(BASE_DIR, "config", "config.json"),
            model_path=os.path.join(BASE_DIR, "captcha", "captcha_model.h5"),
            dataset_path=os.path.join(BASE_DIR, "captcha_dataset")
        )

        checker = HolidayChecker(
            credentials_json=os.path.join(BASE_DIR, "config", "credentials.json"),
            sheet_id="1Djkq8akgmFrBOxnhntJS3JdT5QZFPh5rfii1xzXrBMo"
        )

        scheduler = BlockingScheduler()

        # -------- 執行打卡或排程 ----------
        if command == "signin":
            asyncio.run(run_with_holiday_check("上班打卡", puncher.sign_in, checker, network))

        elif command == "signout":
            asyncio.run(run_with_holiday_check("下班打卡", puncher.sign_out, checker, network))

        elif command == "schedule":
            # 啟動時先排今天的打卡
            asyncio.run(schedule_today_jobs(puncher, checker, scheduler, network))

            # 每天凌晨 00:01 排當天打卡（週一到週五）
            scheduler.add_job(
                lambda: asyncio.run(schedule_today_jobs(puncher, checker, scheduler, network)),
                CronTrigger(hour=0, minute=1, day_of_week="mon-fri"),
                misfire_grace_time=None,  # 無限寬限期（錯過多久都補）
                coalesce=True              # 只補執行最新一次
            )

            print("排程啟動中…")
            scheduler.start()

        else:
            print("未知命令")
            
    finally:
        # -------- 恢復允許睡眠 --------
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
