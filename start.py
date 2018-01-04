"""
Startup script for doorbell
"""
import argparse
from doorbell import run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', dest='config_file', type=str,
                        help='Path to the config yaml file', required=True)
    args = parser.parse_args()
    run(args)

if __name__ == '__main__':
    main()
