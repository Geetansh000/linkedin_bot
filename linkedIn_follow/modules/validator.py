from linkedIn_follow.config.settings import *
from linkedIn_follow.config.personals import *
__validation_file_path = ""


def check_boolean(var: bool, var_name: str) -> bool | ValueError:
    if var == True or var == False:
        return True
    raise ValueError(f'The variable "{var_name}" in "{__validation_file_path}" expects a Boolean input `True` or `False`, not "{var}" of type "{type(var)}" instead!\n\nSolution:\nPlease open "{__validation_file_path}" and update "{var_name}" to either `True` or `False` (case-sensitive, T and F must be CAPITAL/uppercase).\nExample: `{var_name} = True`\n\nNOTE: Do NOT surround Boolean values in quotes ("True")X !\n\n')


def check_string(var: str, var_name: str, options: list = [], min_length: int = 0) -> bool | TypeError | ValueError:
    if not isinstance(var, str):
        raise TypeError(f'Invalid input for {var_name}. Expecting a String!')
    if min_length > 0 and len(var) < min_length:
        raise ValueError(
            f'Invalid input for {var_name}. Expecting a String of length at least {min_length}!')
    if len(options) > 0 and var not in options:
        raise ValueError(
            f'Invalid input for {var_name}. Expecting a value from {options}, not {var}!')
    return True


def validate_settings() -> None | ValueError | TypeError:
    '''
    Validates all variables in the `/config/settings.py` file.
    '''
    global __validation_file_path
    __validation_file_path = "config/settings.py"

    check_string(logs_folder_path, "logs_folder_path", min_length=1)

    check_boolean(run_in_background, "run_in_background")
    check_boolean(disable_extensions, "disable_extensions")
    check_boolean(safe_mode, "safe_mode")
    check_boolean(stealth_mode, "stealth_mode")

def validate_personal() -> None | ValueError | TypeError:
    '''
    Validates all variables in the `/config/personal.py` file.
    '''
    global __validation_file_path
    __validation_file_path = "config/personal.py"

    # Add validations for personal.py variables here when needed
    check_string(SEARCH_STRING, "SEARCH_STRING", min_length=1)
    check_string(your_name, "your_name", min_length=1)
    check_string(years_of_experience, "years_of_experience", min_length=1)
    check_string(resume_link, "resume_link", min_length=1)
    check_string(portfolio_link, "portfolio_link", min_length=1)
