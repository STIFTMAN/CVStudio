import json
from textwrap import shorten
from src.gui.state.error import Info


def format_nested(
    obj,
    *,
    sort_keys: bool = False,
    indent: int = 2,
    key_align: bool = False,
    max_value_len: int = 120,
    max_items: int | None = None,
    max_depth: int | None = None,
    ascii_tree: bool = True
) -> str:
    seen = set()
    if ascii_tree:
        BRANCH, TEE, LAST, INDENT = "|  ", "|- ", "`- ", "   "
    else:
        BRANCH, TEE, LAST, INDENT = "│  ", "├─ ", "└─ ", "   "

    def is_scalar(x):
        return isinstance(x, (str, int, float, bool)) or x is None

    def scalar_to_str(x):
        if isinstance(x, str):
            s = x
        elif isinstance(x, (int, float, bool)) or x is None:
            s = str(x)
        else:
            try:
                s = json.dumps(x, ensure_ascii=False, separators=(",", ":"))
            except TypeError:
                s = str(x)
        if max_value_len and len(s) > max_value_len:
            s = shorten(s, width=max_value_len, placeholder="…")
        return s

    def iter_items(container):
        if isinstance(container, dict):
            items = container.items()
            if sort_keys:
                items = sorted(items, key=lambda kv: str(kv[0]).lower())
            for k, v in items:
                yield str(k), v
        else:
            if isinstance(container, set):
                seq = sorted(container, key=lambda x: str(x))
            else:
                seq = list(container)
            for i, v in enumerate(seq):
                yield f"[{i}]", v

    def walk(x, prefix_parts, depth):
        lines = []
        oid = id(x)
        if isinstance(x, (dict, list, tuple, set)):
            if oid in seen:
                lines.append(Info.FORMAT_NESTED_RECURSIVE_REFERENCE.value)
                return lines
            seen.add(oid)
        if isinstance(x, dict) or isinstance(x, (list, tuple, set)):
            items = list(iter_items(x))
            total = len(items)
            if max_items is not None and total > max_items:
                items = items[:max_items]
                truncated = True
            else:
                truncated = False
            if key_align and items and all(is_scalar(v) for _, v in items):
                width = max(len(lbl) for lbl, _ in items)
            else:
                width = 0

            for idx, (lbl, val) in enumerate(items):
                is_last = idx == len(items) - 1
                connector = LAST if is_last else TEE
                branch_prefix = "".join(BRANCH if p else INDENT for p in prefix_parts[:-1])
                head = branch_prefix + connector

                if is_scalar(val):
                    if width:
                        lines.append(f"{head}{lbl:<{width}} : {scalar_to_str(val)}")
                    else:
                        lines.append(f"{head}{lbl}: {scalar_to_str(val)}")
                else:
                    lines.append(f"{head}{lbl}:")
                    if max_depth is not None and depth >= max_depth:
                        Info.FORMAT_NESTED_RECURSIVE_REFERENCE.value
                        lines.append(branch_prefix + (INDENT if is_last else BRANCH) + Info.FORMAT_NESTED_MAX_DEPTH.value)
                    else:
                        lines += walk(
                            val,
                            prefix_parts + [is_last],
                            depth + 1
                        )
            if truncated:
                branch_prefix = "".join(BRANCH if p else INDENT for p in prefix_parts)
                lines.append(branch_prefix + Info.FORMAT_NESTED_TRUNCATED.value)
        else:
            lines.append(scalar_to_str(x))

        return lines
    return "\n".join(walk(obj, [False], depth=0))
