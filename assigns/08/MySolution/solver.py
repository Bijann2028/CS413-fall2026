"""Type-check and compile the fixed course-language solver once at startup."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'LAMBDA3'))
import lambda3 as L

expression, SOLVER_TYPE = L.d0exp_parse_and_typecheck(
    (HERE / 'queens.lam').read_text(encoding='utf-8'))
runtime = {}
exec(L.d0exp_compile(expression), runtime)
factory = runtime['_lambda_result']
force = runtime['_lambda_lazy_eval']
KINDS = ('try', 'place', 'reject', 'backtrack', 'solution', 'done')


def open_stream(size):
    return factory(size)


def next_event(stream):
    node = force(stream)
    if not node['cons']:
        return None, None
    kind, column, row, board = node['head']
    event = {'event': KINDS[kind]}
    if kind != 5:
        columns = []
        while not runtime['_lambda_list_nilq'](board):
            columns.append(runtime['_lambda_list_head'](board))
            board = runtime['_lambda_list_tail'](board)
        event['board'] = columns[::-1]
    if kind < 4:
        event.update(column=column, row=row)
    return event, node['tail']
