import ast


def validate_python_source(source: str, filename: str = "<strategy>") -> list[str]:
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as error:
        return [f"第 {error.lineno} 行：{error.msg}"]
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    if not classes:
        return ["策略文件中没有类定义"]
    if not any(
        any(
            (isinstance(base, ast.Name) and base.id == "Strategy")
            or (isinstance(base, ast.Attribute) and base.attr == "Strategy")
            for base in node.bases
        )
        for node in classes
    ):
        return ["策略类必须继承 Strategy"]
    return []
