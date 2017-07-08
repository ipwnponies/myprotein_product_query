import mock

from myprotein import parse_cli


@mock.patch('sys.argv', ['program', '--whey'])
def test_parse_cli():
    args = parse_cli()
    assert args.whey
