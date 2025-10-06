import json
from textwrap import shorten


def format_nested(
    obj,
    *,
    sort_keys: bool = False,
    indent: int = 2,
    key_align: bool = False,     # nur für flache Ebenen sinnvoll; i. d. R. False lassen
    max_value_len: int = 120,    # einzelne (skalare) Werte werden auf diese Länge gekürzt
    max_items: int | None = None,  # pro Container-Ebene höchstens so viele Einträge
    max_depth: int | None = None,  # maximal in die Tiefe gehen (None = unbegrenzt)
    ascii_tree: bool = False     # True => "-", "|-" statt Unicode-Baumzeichen
) -> str:
    """Gibt einen schön formatierten Baum-String zurück."""
    seen = set()

    # Baumzeichen
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
            # Fallback für Objekte
            try:
                s = json.dumps(x, ensure_ascii=False, separators=(",", ":"))
            except TypeError:
                s = str(x)
        if max_value_len and len(s) > max_value_len:
            s = shorten(s, width=max_value_len, placeholder="…")
        return s

    def iter_items(container):
        """Erzeugt (label, value)-Paare für dicts und sequenzen."""
        if isinstance(container, dict):
            items = container.items()
            if sort_keys:
                items = sorted(items, key=lambda kv: str(kv[0]).lower())
            for k, v in items:
                yield str(k), v
        else:
            # Sequenzen: Label sind Indizes
            # Für Sets/tupel/list – Sets vorher sortierbar machen
            if isinstance(container, set):
                seq = sorted(container, key=lambda x: str(x))
            else:
                seq = list(container)
            for i, v in enumerate(seq):
                yield f"[{i}]", v

    def walk(x, prefix_parts, depth):
        lines = []

        # Rekursion/zyklische Referenzen verhindern
        oid = id(x)
        if isinstance(x, (dict, list, tuple, set)):
            if oid in seen:
                lines.append("↻ <rekursive Referenz>")
                return lines
            seen.add(oid)

        # Container?
        if isinstance(x, dict) or isinstance(x, (list, tuple, set)):
            items = list(iter_items(x))
            total = len(items)
            if max_items is not None and total > max_items:
                items = items[:max_items]
                truncated = True
            else:
                truncated = False

            # Ausrichtung für Keys auf dieser Ebene (optional)
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
                        # hübscher, wenn Wert direkt nach ": " kommt
                        lines.append(f"{head}{lbl}: {scalar_to_str(val)}")
                else:
                    # Überschrift-Zeile für verschachtelten Wert
                    lines.append(f"{head}{lbl}:")
                    # Tiefe prüfen
                    if max_depth is not None and depth >= max_depth:
                        lines.append(branch_prefix + (INDENT if is_last else BRANCH) + "… (Tiefe begrenzt)")
                    else:
                        # Rekursiv weiter; für die nächste Ebene merken, ob dieser Ast "letzter" ist
                        lines += walk(
                            val,
                            prefix_parts + [is_last],
                            depth + 1
                        )
            if truncated:
                branch_prefix = "".join(BRANCH if p else INDENT for p in prefix_parts)
                lines.append(branch_prefix + "… (weitere Einträge ausgelassen)")
        else:
            # Skalar direkt ausgeben
            lines.append(scalar_to_str(x))

        return lines

    # Wurzelebene: keine Einrückung, wir starten mit einer Liste mit einem "letzten"-Flag (egal)
    return "\n".join(walk(obj, [True], depth=0))
