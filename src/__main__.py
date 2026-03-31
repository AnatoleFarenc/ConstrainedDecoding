from src.Generator import Generator
from src.Menu import Menu
from src.parsing import parse_argument, check_files
import sys
from src import ID_FUNC, ID_CALL, ID_OUTPUT, MONO_TEST, FUNC_SHEMA, CALL_SHEMA

# try:
#     prompt = Prompt(func_def_paht, func_ID_call)
# except FileNotFoundError as e:
#     print(e)
#     sys.exit()


def main():
    """ Entry for the program """
    arguments = [
        "data/input/functions_definition.json",
        "data/input/function_calling_tests.json",
        "data/output/function_calling_results.json",
        "-1"
    ]
    try:
        arguments = parse_argument(arguments)
    except ValueError as e:
        print(e)
        print("Default value assigned")
    try:
        check_files(arguments[ID_FUNC], FUNC_SHEMA)
        check_files(arguments[ID_CALL], CALL_SHEMA)
    except (FileNotFoundError, ValueError) as e:
        print(e)
        print("End of programe")
        sys.exit()

    if len(sys.argv) == 1:
        app = Menu(arguments[ID_FUNC], arguments[ID_CALL],
                   arguments[ID_OUTPUT])
        app.run()
    else:
        gen = Generator(arguments[ID_FUNC], arguments[ID_CALL],
                        arguments[ID_OUTPUT])
        # gen.generate_responce(gen.pr.user_prompts[2])
        if arguments[MONO_TEST] == "-1":
            gen.generate_all_responce()
        else:
            try:
                idx = int(arguments[MONO_TEST])
                if idx < 0 or idx >= len(gen.pr.user_prompts):
                    raise ValueError()
            except ValueError:
                print("ERROR: Invalid value for --mono_test: "
                      f"{arguments[MONO_TEST]}")
                sys.exit()
            gen.generate_responce(gen.pr.user_prompts[idx])
            try:
                gen.write_responce_json()
            except ValueError as e:
                print(e)
                sys.exit()


if __name__ == "__main__":
    main()
