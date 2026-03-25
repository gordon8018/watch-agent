# main.py
from config import parse_args

if __name__ == "__main__":
    args = parse_args()
    print(f"session={args.session}, status_dir={args.status_dir}")
