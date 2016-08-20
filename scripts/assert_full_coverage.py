import re
import sys


def main():
    failed = False
    for line in sys.stdin:
        sys.stdout.write(line)
        if failed:
            continue
        coverage_match = re.match(r'TOTAL .* (\d+)%', line)
        tests_failed_match = re.match(r'FAILED \(errors=[0-9]*\)', line)
        if coverage_match and coverage_match.group(1) != '100':
            failed = True
        elif tests_failed_match:
            sys.exit(-1)
    if failed:
        print 'Your test coverage is not 100%'
        sys.exit(-1)

if __name__ == '__main__':
    main()
