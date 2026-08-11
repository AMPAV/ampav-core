import argparse
import logging
from pathlib import Path

from ampav.core.logging import LOG_FORMAT, ListLoggingHandler
from ampav.core.schema import load_ampav_file
from ampav.core.schema.compound import CompoundOutput
from ampav.core.utils import dump_data


def cli_tool():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Turn on debug logging')
    parser.add_argument('--allow_pickle', action='store_true', help='Allow loading pickle-formatted file')
    subp = parser.add_subparsers(dest='command', required=True)
    cmd = subp.add_parser('list', help="List contents of ampav file")
    cmd.add_argument('ampav_file', type=Path, help="ampav file")
    cmd = subp.add_parser('remove', help="Remove outputs from compound file")
    cmd.add_argument('ampav_file', type=Path, help="ampav file")
    cmd.add_argument('--format', choices=['yaml', 'json', 'pickle'], default='yaml', help="Output file type (default yaml)")
    cmd.add_argument('--output', type=Path, required=True, help="new ampav file")    
    cmd.add_argument('outputs', type=str, nargs='+', help="Outputs to remove")
    cmd = subp.add_parser('copy', help="copy outputs from compound file")
    cmd.add_argument('ampav_file', type=Path, help="ampav file")
    cmd.add_argument('--format', choices=['yaml', 'json', 'pickle'], default='yaml', help="Output file type (default yaml)")
    cmd.add_argument('--output', type=Path, required=True, help="new ampav file")    
    cmd.add_argument('outputs', type=str, nargs='+', help="Outputs to copy")
    args = parser.parse_args()

    logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG if args.debug else logging.INFO)

    logging.info(f"Loading data file {args.ampav_file}")
    data = load_ampav_file(args.ampav_file, args.allow_pickle)

    loghandler = ListLoggingHandler(data.messages)
    logging.getLogger().addHandler(loghandler)

    if data.output.ampav_format != "compound/1":
        logging.error(f"{args.ampav_file} is not a a compound file: {data.ampav_format}")
        exit(1)

    match args.command:
        case 'list':
            items = [(k, v.ampav_format) for k,v in data.output.outputs.items()]
            nlen = max([len(x[0]) for x in items])
            tlen = max([len(x[1]) for x in items])
            print(f"{'Output'.ljust(nlen)}  {'Type'.ljust(tlen)}")
            print(f"{'-'*nlen}  {'-'*(tlen)}")
            for k, v in items:
                print(f"{k.ljust(nlen)}  {v.ljust(tlen)}")

        case 'remove':
            for item in args.outputs:
                if item in data.output.outputs:
                    logging.info(f"Removing output {item} from {args.ampav_file}")                    
                    data.output.outputs.pop(item)
                else:
                    logging.warning(f"Output {item} is not in the file")
            logging.info(f"Writing {args.output} in {args.format}")
            dump_data(data, args.format, args.output)

        case 'copy':
            for k, v in [(k, v) for k,v in data.output.outputs.items()]:
                if k not in args.outputs:
                    # remove it, we don't want it
                    data.output.outputs.pop(k, None)
                else:
                    logging.info(f"Copying {k} from {args.ampav_file}")
                    
            logging.info(f"Writing {args.output} in {args.format}")
            dump_data(data, args.format, args.output)

