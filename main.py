from config import parse_args
from dashboard.app import WatchApp

if __name__ == "__main__":
    args = parse_args()
    app = WatchApp(session=args.session, status_dir=args.status_dir)
    app.run()
