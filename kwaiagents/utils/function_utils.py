import docstring_parser


def transform_to_openai_function(func):
    parsed = docstring_parser.parse(func.__doc__)

    # Extract descriptions, args, and returns
    description = parsed.short_description

    args = {}
    for param in parsed.params:
        args[param.arg_name] = {
            "type": param.type_name,
            "description": param.description
        }

    returns = {
        "description": parsed.returns.description if hasattr(parsed.returns, "returns") else "",
        "type": parsed.returns.type_name if hasattr(parsed.returns, "type_name") else ""
    }

    return {
        "name": func.name if hasattr(func, "name") else func.__name__,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": args
        },
        "returns": returns,
        "required": list(args.keys())
    }
