import argparse
import ast
import pathlib
import random
import re
import string


class ReduceBinOp(ast.NodeTransformer):
    def visit_BinOp(self, node):
        """
        It checks for all BinOp and tries to reduce de expression.
        :param node: The BinOp node to check.
        :return: If the function can reduce the BinOp returns a constant, otherwise returns the same node.
        """
        constant = ""
        try:
            constant = ast.unparse(node)
            evaluation = eval(constant, {'__builtins__': None}, {})
            return ast.Constant(evaluation)
        except:
            math_operation_pattern = "[\d]+[\d\ \+\-\*\/\%]+[\d]"
            results = re.findall(math_operation_pattern, constant)
            for result in results:
                evaluation = eval(result, {'__builtins__': None}, {})
                constant = constant.replace(result, str(evaluation), 1)
            new_node = ast.parse(constant)
            return new_node.body[0].value


class ExpandString(ast.NodeTransformer):
    def visit_Constant(self, node):
        """
        It looks for all strings and divide them.
        :param node: A constant type node.
        :return: A BinOp node with a sum of the strings.
        """
        if isinstance(node.value, str) and len(node.value) > 1 and not node.value.startswith("__") and \
                not node.value.endswith("__"):
            substrings = self.split_string(node.value)
            new_code = (chr(34) + chr(34) + chr(34) +
                        (chr(34) + chr(34) + chr(34) + "+" + chr(34) + chr(34) + chr(34)).join(substrings) +
                        chr(34) + chr(34) + chr(34))
            new_code = new_code.replace("\\", "\\\\")
            new_code = new_code.replace(chr(0), "\\x00")
            new_code = new_code.replace(chr(9), "\\t")
            new_code = new_code.replace(chr(10), "\\n")
            new_node = ast.parse(new_code)
            return new_node.body[0].value
        return node

    def split_string(self, string_data):
        """
        It splits a string in a random number of substrings.
        :param string_data: String to be split.
        :return: A list of substrings.
        """
        substrings = []
        while len(string_data) > 0:
            n = random.randint(1, len(string_data))
            substrings.append(string_data[:n])
            string_data = string_data[n:]
        return substrings


class RepairJoinedStr(ast.NodeTransformer):
    def visit_JoinedStr(self, node: ast.JoinedStr):
        """
        It fixes the JoinedStr class.
        :param node: A JoinedStr node.
        :return: A JoinedStr node without BinOp.
        """
        final_values = []
        for value in node.values:
            if isinstance(value, ast.BinOp):
                binop_string = ast.unparse(value)
                joined_string = eval(binop_string)
                final_values.append(ast.Constant(joined_string))
            else:
                final_values.append(value)
        node.values = final_values
        return node


class ExpandInteger(ast.NodeTransformer):
    def visit_Constant(self, node):
        """
        It looks for all integers and generates a math expression that returns the original integer.
        :param node: A constant type node.
        :return: A BinOp node with a math expression that when is valuated returns the original integer value.
        """
        if isinstance(node.value, int) and not isinstance(node.value, bool):
            code = ""
            while True:
                try:
                    code = self.get_expression(node.value)
                    break
                except ZeroDivisionError:
                    continue
            new_node = ast.parse(code)
            return new_node.body[0].value
        return node

    def get_expression(self, value):
        """
        It generates a math expression that has the same value as an integer.
        :param value: An integer.
        :return: Math expression that has the same value as an integer.
        """
        random_numbers = [str(random.randint(0, 1000)) for _ in range(random.randint(2, 10))]
        symbols = ["+", "-", "*", "%", "//"]
        operation = []
        for number in random_numbers:
            operation.append(number)
            symbol_index = random.randint(0, len(symbols) - 1)
            operation.append(symbols[symbol_index])
        operation.pop(len(operation) - 1)
        code = "".join(operation)
        result = eval(code)
        last = result - value
        if last > 0:
            code += "-" + str(last)
        elif last < 0:
            code += "+" + str(abs(last))
        return code


class ImportUpdater(ast.NodeTransformer):
    def __init__(self, modules, relations):
        self.modules = modules
        self.relations = relations

    def visit_Attribute(self, node):
        """
        Updates the attributes of imports
        :param node: An ast.Attribute node
        :return: An ast.Attribute node
        """
        attribute = ast.unparse(node)
        point_position = attribute.rfind(".")
        if point_position == -1:
            return node
        attribute = attribute[:point_position]
        if attribute in self.modules:
            node.attr = self.relations[node.attr]
        return node


class DataClass:
    """
    It stores the relevant names of a class
    """
    def __init__(self):
        # Name of the class
        self.class_name = ""

        # List of attributes
        self.attributes = []

        # List of the functions
        self.functions = []

        # Dictionary that stores every local variable in each function
        self.local_variables = {}

        # Dictionary with the old names of the variables of the class as keys and the new generated names as values
        self.name_relations = {}


global_variables = []
function_names = []
local_variables = {}
classes = []


def main():
    parser = argparse.ArgumentParser(
        description="Mutates the code of python files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "file",
        metavar='File(s)',
        type=str,
        help="File(s) to be mutated",
        nargs="+"
    )
    args = parser.parse_args()

    mutate(args.file)


def mutate(files):
    """
    It reads a python source code file and mutates the code.
    :return:
    """

    # Obtain a list of the modules in the files
    modules = [file.replace(".py", "").replace(chr(47), ".") for file in files]

    # Obtain a list of the abstract syntax trees
    trees = get_trees(files)

    # Performs modifications in the nodes of a list of trees
    trees = expand_nodes(trees)

    # Get the information about the variable names
    exclusions = manage_names(trees)

    # Generate the names of the global variables and functions
    name_relations = create_name_relations(exclusions)

    # Change the variable names
    trees = modify_names(trees, exclusions, name_relations, modules)

    # Change the position of the functions
    trees = update_function_locations(trees)

    # Generates the code of the modified trees
    sources = [ast.unparse(tree) for tree in trees]

    # Adds random comments in the code
    sources = [add_comments(source) for source in sources]

    # Saves the final code
    create_final_directory(files)
    save_source_code(files, sources)


def get_trees(files):
    """
    This function reads the source code files and parses it to generate a list of the abstract syntax trees
    :param files: A list of files with source code
    :return: A list of with the abstract syntax trees of the source files
    """
    trees = []
    for file in files:
        with open(file, "r") as f:
            source = f.read()
        tree = ast.parse(source)
        trees.append(tree)
    return trees


def expand_nodes(trees):
    """
    It performs the modification of the nodes of a list of trees.
    :param trees: A list of abstract syntax trees
    :return: A list with modified abstract syntax trees
    """
    result = []
    for tree in trees:
        # Perform some expansions in the tree
        tree = ast.fix_missing_locations(ReduceBinOp().visit(tree))
        tree = ast.fix_missing_locations(ExpandString().visit(tree))
        tree = ast.fix_missing_locations(RepairJoinedStr().visit(tree))
        tree = ast.fix_missing_locations(ExpandInteger().visit(tree))

        # Change the pass locations
        delete_pass(tree)
        add_pass(tree)
        fix_pass(tree)

        # Save the result
        result.append(tree)
    return result


def delete_pass(tree):
    """
    It deletes the reserved word "pass" from the bodies where it does not do anything
    :param tree: The abstract syntax tree to walk
    :return: This function modifies the pointer of tree variable so does not return anything
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Module) or isinstance(node, ast.If) or isinstance(node, ast.For) or \
                isinstance(node, ast.While) or isinstance(node, ast.Try) or isinstance(node, ast.AsyncFor) or \
                isinstance(node, ast.FunctionDef) or isinstance(node, ast.ClassDef) or \
                isinstance(node, ast.AsyncFunctionDef):
            to_remove = []
            for element in node.body:
                if isinstance(element, ast.Pass) and len(node.body) > 1:
                    to_remove.append(element)
            for element in to_remove:
                node.body.remove(element)
        if isinstance(node, ast.If) or isinstance(node, ast.For) or isinstance(node, ast.While) or \
                isinstance(node, ast.Try) or isinstance(node, ast.AsyncFor):
            to_remove = []
            for element in node.orelse:
                if isinstance(element, ast.Pass) and len(node.orelse) > 1:
                    to_remove.append(element)
            for element in to_remove:
                node.body.append(element)
        if isinstance(node, ast.Try):
            to_remove = []
            for element in node.finalbody:
                if isinstance(element, ast.Pass) and len(node.finalbody) > 1:
                    to_remove.append(element)
            for element in to_remove:
                node.body.remove(element)


def add_pass(tree):
    """
    It adds the reserved word "pass" in the body of the nodes of an AST
    :param tree: The abstract syntax tree to walk
    :return: This function modifies the pointer of tree variable so does not return anything
    """
    probability = 0.5
    for node in ast.walk(tree):
        if isinstance(node, ast.Module) or isinstance(node, ast.If) or isinstance(node, ast.For) or\
                isinstance(node, ast.While) or isinstance(node, ast.Try) or isinstance(node, ast.AsyncFor) or\
                isinstance(node, ast.FunctionDef) or isinstance(node, ast.ClassDef) or\
                isinstance(node, ast.AsyncFunctionDef):
            position = 0
            for i in range(len(node.body)):
                if random.random() < probability:
                    k = random.randint(1, 5)
                    for j in range(k):
                        node.body.insert(position, ast.Pass())
                    position = i + k + position
        if isinstance(node, ast.If) or isinstance(node, ast.For) or isinstance(node, ast.While) or \
                isinstance(node, ast.Try) or isinstance(node, ast.AsyncFor):
            position = 0
            for i in range(len(node.orelse)):
                if random.random() < probability:
                    k = random.randint(1, 5)
                    for j in range(k):
                        node.orelse.insert(position, ast.Pass())
                    position = i + k + position
        if isinstance(node, ast.Try):
            position = 0
            for i in range(len(node.finalbody)):
                if random.random() < probability:
                    k = random.randint(1, 5)
                    for j in range(k):
                        node.finalbody.insert(position, ast.Pass())
                    position = i + k + position


def fix_pass(tree):
    """
    It fixes the AST deleting the initial "pass" when __future__ is imported.
    :param tree: The abstract syntax tree to walk.
    :return: This function modifies the pointer of tree variable so does not return anything.
    """
    pass_position = []
    imports_and_pass = {}
    pass_to_remove = []
    for i in range(len(tree.body)):
        node = tree.body[i]
        if isinstance(node, ast.Pass):
            pass_position.append(i)
        elif isinstance(node, ast.ImportFrom) and node.module == "__future__":
            imports_and_pass[i] = pass_position.copy()
            pass_position.clear()
        elif isinstance(node, ast.Import) and node.names[0].name == "__future__":
            imports_and_pass[i] = pass_position.copy()
            pass_position.clear()
    for values in imports_and_pass.values():
        pass_to_remove += values
    pass_to_remove = sorted(pass_to_remove, reverse=True)
    for position in pass_to_remove:
        del tree.body[position]


def manage_names(trees):
    """
    It obtains the names and its type (local, global, function...) and stores this information in some global variables.
    :param trees: A list of abstract syntax trees
    :return: A list with all the variable names
    """
    exclusions = []
    for tree in trees:
        # Get the variables names of the source code
        get_names_info(tree)

        # Stores all local variable names
        unclassified_local_variables = [item for sublist in local_variables.values() for item in sublist]

        for data_class in classes:
            # Exclude the variable names detected in a class removing the magic methods and the "self" word
            discard_necessary_names(data_class)

            # Updates the list of local variables
            unclassified_local_variables += [item for sublist in data_class.local_variables.values() for item in
                                             sublist]

        # Removes the duplicated values of the list of local variables
        unclassified_local_variables = list(set(unclassified_local_variables))

        # Stores the global variables, function names and local variables.
        # This is used to avoid to create the same names.
        exclusions += global_variables + function_names + unclassified_local_variables
    return list(set(exclusions))


def get_names_info(tree, function_name="", data_class=None):
    """
    It gets the names of variables in an abstract syntax tree.
    :param tree: The abstract syntax tree to walk
    :param function_name: The function name that is being analyzed
    :param data_class: The class that is being analyzed
    :return: It modifies the variables global_variables, function_names, local_variables so does not return anything
    """
    for part in tree.body:
        classify_names(part, function_name, data_class)

    # If the statement has an "else" or "elif"
    if isinstance(tree, ast.If) or isinstance(tree, ast.For) or isinstance(tree, ast.While) or \
            isinstance(tree, ast.Try) or isinstance(tree, ast.AsyncFor):
        for part in tree.orelse:
            classify_names(part, function_name, data_class)

    # If the statement has a "finally"
    if isinstance(tree, ast.Try):
        for part in tree.finalbody:
            classify_names(part, function_name, data_class)


def classify_names(part, function_name, data_class=None):
    """
    It classifies the variables in global, local or function names
    :param part: The abstract syntax tree to walk
    :param function_name: The function name that is being analyzed
    :param data_class: The class that is being analyzed
    :return: It modifies the variables global_variables, function_names, local_variables so does not return anything
    """
    if isinstance(part, ast.Name) and not function_name and data_class is None:
        global_variables.append(part.id)
    elif isinstance(part, ast.Name) and function_name and data_class is None:
        local_variables[function_name] = local_variables.get(function_name, []) + [part.id]
    elif isinstance(part, ast.Name) and not function_name and data_class is not None:
        data_class.attributes.append(part.id)
    elif isinstance(part, ast.Name) and function_name and data_class is not None:
        data_class.local_variables[function_name] = data_class.local_variables.get(function_name, []) + [part.id]
    elif isinstance(part, ast.arg) and data_class is None:
        local_variables[function_name] = local_variables.get(function_name, []) + [part.arg]
    elif isinstance(part, ast.arg) and data_class is not None:
        data_class.local_variables[function_name] = data_class.local_variables.get(function_name, []) + [part.arg]
    elif isinstance(part, ast.UnaryOp):
        classify_names(part.operand, function_name, data_class)
    elif isinstance(part, ast.BinOp):
        classify_names(part.left, function_name, data_class)
        classify_names(part.right, function_name, data_class)
    elif isinstance(part, ast.BoolOp):
        for value in part.values:
            classify_names(value, function_name, data_class)
    elif isinstance(part, ast.Compare):
        classify_names(part.left, function_name, data_class)
        for comparator in part.comparators:
            classify_names(comparator, function_name, data_class)
    elif isinstance(part, ast.Assign):
        for target in part.targets:
            classify_names(target, function_name, data_class)
    elif isinstance(part, ast.Attribute) and data_class is None:
        classify_names(part.value, function_name)
    elif isinstance(part, ast.Attribute) and data_class is not None:
        if isinstance(part.value, ast.Name) and part.value.id == "self":
            data_class.attributes.append(part.attr)
    elif isinstance(part, ast.NamedExpr) or isinstance(part, ast.AnnAssign) or isinstance(part, ast.AugAssign):
        classify_names(part.target, function_name, data_class)
    elif isinstance(part, ast.Tuple) or isinstance(part, ast.List) or isinstance(part, ast.Set):
        for elt in part.elts:
            classify_names(elt, function_name, data_class)
    elif isinstance(part, ast.If) or isinstance(part, ast.While):
        get_names_info(part, function_name, data_class)
    elif isinstance(part, ast.Try):
        get_names_info(part, function_name, data_class)
        for handler in part.handlers:
            classify_names(handler, function_name, data_class)
    elif isinstance(part, ast.ExceptHandler):
        get_names_info(part, function_name, data_class)
    elif isinstance(part, ast.With) or isinstance(part, ast.AsyncWith):
        for item in part.items:
            classify_names(item.context_expr, function_name, data_class)
            classify_names(item.optional_vars, function_name, data_class)
        get_names_info(part, function_name, data_class)
    elif isinstance(part, ast.ListComp) or isinstance(part, ast.SetComp) or isinstance(part, ast.GeneratorExp):
        classify_names(part.elt, function_name, data_class)
        for generator in part.generators:
            classify_names(generator, function_name, data_class)
    elif isinstance(part, ast.DictComp):
        classify_names(part.key, function_name, data_class)
        classify_names(part.value, function_name, data_class)
        for generator in part.generators:
            classify_names(generator, function_name, data_class)
    elif isinstance(part, ast.comprehension):
        classify_names(part.target, function_name, data_class)
        classify_names(part.iter, function_name, data_class)
        for comparator in part.ifs:
            classify_names(comparator, function_name, data_class)
    elif isinstance(part, ast.For) or isinstance(part, ast.AsyncFor):
        classify_names(part.target, function_name, data_class)
        get_names_info(part, function_name, data_class)
    elif isinstance(part, ast.ClassDef):
        class_info = DataClass()
        class_info.class_name = part.name
        get_names_info(part, function_name, class_info)
        classes.append(class_info)
    elif isinstance(part, ast.arguments):
        for posonlyarg in part.posonlyargs:
            classify_names(posonlyarg, function_name, data_class)
        for arg in part.args:
            classify_names(arg, function_name, data_class)
        for kwonlyarg in part.kwonlyargs:
            classify_names(kwonlyarg, function_name, data_class)
        if part.kwarg:
            classify_names(part.kwarg, function_name, data_class)
        if part.vararg:
            classify_names(part.vararg, function_name, data_class)
    elif (isinstance(part, ast.FunctionDef) or isinstance(part, ast.AsyncFunctionDef)) and data_class is None:
        function_names.append(part.name)
        classify_names(part.args, part.name)
        get_names_info(part, part.name)
    elif (isinstance(part, ast.FunctionDef) or isinstance(part, ast.AsyncFunctionDef)) and data_class is not None:
        data_class.functions.append(part.name)
        classify_names(part.args, part.name, data_class)
        get_names_info(part, part.name, data_class)


def discard_necessary_names(class_data: DataClass):
    """
    It removes all magic methods and all visit_ methods stored in a DataClass object.
    :param class_data: Is the DataClass object obtained from an AST
    :return: Modifies the pointer to class_data
    """
    # remove magic and visit_ methods
    for function in class_data.functions:
        if function.startswith("__") and function.endswith("__"):
            class_data.functions.remove(function)
        elif function.startswith("visit_"):
            class_data.functions.remove(function)
    # remove self name
    for function in class_data.local_variables.keys():
        if "self" in class_data.local_variables[function]:
            class_data.local_variables[function].remove("self")
    # remove functions without local variables
    function_to_remove = []
    for function, variables in class_data.local_variables.items():
        if not variables:
            function_to_remove.append(function)
    for function in function_to_remove:
        class_data.local_variables.pop(function)


def create_name_relations(exclusions):
    """
    This function manages the creation of the names of global variables, functions, classes and functions of a class.
    :param exclusions: A list with names that cannot be generated
    :return: A dictionary with the old names as a key and the new names as a value
    """
    name_relations = {}

    for old_name in global_variables:
        new_name = generate_name(exclusions)
        name_relations[old_name] = new_name
        exclusions.append(new_name)

    for old_name in function_names:
        new_name = generate_name(exclusions)
        name_relations[old_name] = new_name
        exclusions.append(new_name)

    for data_class in classes:
        new_name = generate_name(exclusions)
        name_relations[data_class.class_name] = new_name
        exclusions.append(new_name)

    for data_class in classes:
        for function in data_class.functions:
            new_name = generate_name(exclusions)
            data_class.name_relations[function] = new_name
            exclusions.append(new_name)

        for attribute in data_class.attributes:
            new_name = generate_name(exclusions)
            data_class.name_relations[attribute] = new_name
            exclusions.append(new_name)

    return name_relations


def modify_names(trees, exclusions, name_relations, modules):
    """
    It changes the variable names in a list of abstract syntax trees
    :param trees: A list of abstract syntax trees
    :param exclusions: A list with names that cannot be generated
    :param name_relations: A dictionary with the information of how the names are changed
    :param modules: A list with the modules imported between the abstract syntax tree
    :return: A list of abstract syntax trees with the variable names changed
    """
    result = []
    for tree in trees:
        # Updates the variable names related to classes
        for data_class in classes:
            update_attributes(tree, data_class)
            update_class_local_variables(tree, data_class, exclusions)
            update_class_functions_name(tree, data_class)
            change_class_name(tree, data_class.class_name, name_relations)

        # Updates the variables not related with classes
        update_global_variables(tree, name_relations)
        update_local_variables(tree, exclusions)
        update_functions_name(tree, name_relations)

        # Updates the functions and variables imported in an ImportFrom
        update_import_from(tree, modules, name_relations)

        # Updates the functions and variables imported in as Import
        tree = ast.fix_missing_locations(ImportUpdater(modules, name_relations).visit(tree))

        # Save the modified tree
        result.append(tree)
    return result


def update_attributes(tree, data_class):
    """
    It changes all names of attributes of a class.
    :param tree: The abstract syntax tree to walk
    :param data_class: The names of class to be changed
    :return: This function modifies the pointer of tree variable and modifies the exclusion list adding the new names of
    the attributes
    """
    for attribute in data_class.attributes:
        new_name = data_class.name_relations.get(attribute)
        change_attribute_name(tree, attribute, new_name, data_class.class_name)


def change_attribute_name(tree, old_name, new_name, class_name):
    """
    It changes the attribute name of a class.
    :param tree: The abstract syntax tree to walk
    :param old_name: The attribute name to be changed
    :param new_name: The new name of the old attribute
    :param class_name: Class name where the attribute is located
    :return: This function modifies the pointer of tree variable so does not return anything
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == old_name:
            node.attr = new_name
        elif isinstance(node, ast.ClassDef) and node.name == class_name:
            for part in node.body:
                if not isinstance(part, ast.Assign):
                    continue
                for target in part.targets:
                    if isinstance(target, ast.Name) and target.id == old_name:
                        target.id = new_name


def generate_name(exclusions):
    """
    It creates a string different from a list of other names
    :param exclusions: List with names that the result will not be equal
    :return: A random string
    """
    new_name = get_random_name()
    while new_name in exclusions:
        new_name = get_random_name()
    return new_name


def get_random_name(min_len=5, max_len=15):
    """
    It generates a random string which has a length between min_len and max_len (default values are 5 and 15)
    :param min_len: Minimum possible length of the returned name
    :param max_len: Maximum possible length of the returned name
    :return: A random string with a length between min_len and max_len
    """
    length = random.randint(min_len, max_len)
    result_str = ''.join(random.choice(string.ascii_letters) for i in range(length))
    return result_str


def update_class_local_variables(tree, data_class, exclusions):
    """
    It changes all names of local variables in a class
    :param tree: The abstract syntax tree to walk
    :param data_class: Class data to be changed
    :param exclusions: The list of excluded names
    :return: This function modifies the pointer of tree variable so does not return anything
    """
    for function in data_class.local_variables.keys():
        for local_variable in data_class.local_variables.get(function):
            new_name = generate_name(exclusions)
            change_class_local_variable(tree, local_variable, new_name, data_class.class_name, function)
            exclusions.append(new_name)


def change_class_local_variable(tree, old_name, new_name, class_name, function):
    """
    It changes the name of a local variable inside a function class
    :param tree: The abstract syntax tree to walk
    :param old_name: The local variable name to be changed
    :param new_name: The new name of the old local variable
    :param class_name: Class name where the local variable is located
    :param function: Function name where the local variable is located
    :return: This function modifies the pointer of tree variable so does not return anything
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if not node.name == class_name:
            continue
        for class_def_part in ast.walk(node):
            if not isinstance(class_def_part, ast.FunctionDef):
                continue
            if class_def_part.name != function:
                continue
            for argument in class_def_part.args.args:
                if argument.arg == old_name:
                    argument.arg = new_name
            for posonlyarg in class_def_part.args.posonlyargs:
                if posonlyarg.arg == old_name:
                    posonlyarg.arg = new_name
            for kwonlyarg in class_def_part.args.kwonlyargs:
                if kwonlyarg.arg == old_name:
                    kwonlyarg.arg = new_name
            if class_def_part.args.kwarg:
                if class_def_part.args.kwarg.arg == old_name:
                    class_def_part.args.kwarg.arg = new_name
            if class_def_part.args.vararg:
                if class_def_part.args.vararg.arg == old_name:
                    class_def_part.args.vararg.arg = new_name
            for function_def_part in ast.walk(class_def_part):
                if isinstance(function_def_part, ast.Name) and function_def_part.id == old_name:
                    function_def_part.id = new_name


def update_class_functions_name(tree, data_class):
    """
    It changes all names of functions in a class
    :param tree: The abstract syntax tree to walk
    :param data_class: Class data to be changed
    :return: This function modifies the pointer of tree variable so does not return anything
    """
    for function in data_class.functions:
        new_name = data_class.name_relations.get(function)
        change_class_function_name(tree, function, new_name, data_class.class_name)


def change_class_function_name(tree, old_name, new_name, class_name):
    """
    It changes the name of a function of a class
    :param tree: The abstract syntax tree to walk
    :param old_name: The function name to be changed
    :param new_name: The new name of the old function
    :param class_name: Class name where the local variable is located
    :return: This function modifies the pointer of tree variable so does not return anything
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if not node.name == class_name:
            continue
        for class_def_part in ast.walk(node):
            if isinstance(class_def_part, ast.FunctionDef) and class_def_part.name == old_name:
                class_def_part.name = new_name
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == old_name:
            node.attr = new_name


def change_class_name(tree, old_name, name_relations):
    """
    It changes the class name and all his declarations
    :param tree: The abstract syntax tree to walk
    :param old_name: The class name to be changed
    :param name_relations: A dictionary with the information of how the names are changed
    :return: This function modifies the pointer of tree variable so does not return anything
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == old_name:
            node.name = name_relations.get(old_name)
        elif isinstance(node, ast.Name) and node.id == old_name:
            node.id = name_relations.get(old_name)


def update_global_variables(tree, name_relations):
    """
    It changes the names of the global variables
    :param tree: The abstract syntax tree to walk
    :param name_relations: A dictionary with the information of how the names are changed
    :return: This function modifies the pointer of tree variable so does not return anything
    """
    for global_variable in global_variables:
        new_name = name_relations.get(global_variable)
        change_global_variable(tree, global_variable, new_name)


def change_global_variable(tree, old_name, new_name):
    """
    It walks the abstract syntax tree changing all occurrences of a variable to a new_name.
    :param tree: The abstract syntax tree to walk
    :param old_name: The variable name to be changed
    :param new_name: The new name of the old variable
    :return: This function modifies the pointer of tree variable so does not return anything
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if node.id == old_name:
                node.id = new_name


def update_local_variables(tree, exclusions):
    """
    It changes the names of the local variables
    :param tree: The abstract syntax tree to walk
    :param exclusions: The list of excluded names
    :return: This function modifies the pointer of tree variable so does not return anything
    """
    for function in local_variables.keys():
        for local_variable in local_variables.get(function):
            new_name = generate_name(exclusions)
            change_local_variables(tree, local_variable, new_name, function)
            exclusions.append(new_name)


def change_local_variables(tree, old_name, new_name, function_name):
    """
    It changes all occurrences of the name of a variable in a specific function.
    :param tree: The abstract syntax tree to walk
    :param old_name: The variable name to be changed
    :param new_name: The new name of the old variable
    :param function_name: The name of the function where the old variable is.
    :return: This function modifies the pointer of tree variable so does not return anything
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name != function_name:
            continue
        for argument in node.args.args:
            if argument.arg == old_name:
                argument.arg = new_name
        for posonlyarg in node.args.posonlyargs:
            if posonlyarg.arg == old_name:
                posonlyarg.arg = new_name
        for kwonlyarg in node.args.kwonlyargs:
            if kwonlyarg.arg == old_name:
                kwonlyarg.arg = new_name
        if node.args.kwarg:
            if node.args.kwarg.arg == old_name:
                node.args.kwarg.arg = new_name
        if node.args.vararg:
            if node.args.vararg.arg == old_name:
                node.args.vararg.arg = new_name
        for part in ast.walk(node):
            if isinstance(part, ast.Name):
                if part.id == old_name:
                    part.id = new_name


def update_functions_name(tree, name_relations):
    """
    It changes the names of the functions
    :param tree: The abstract syntax tree to walk
    :param name_relations: A dictionary with the information of how the names are changed
    :return: This function modifies the pointer of tree variable so does not return anything
    """
    for function in function_names:
        new_name = name_relations.get(function)
        change_function_name(tree, function, new_name)


def change_function_name(tree, old_name, new_name):
    """
    It changes all occurrences of the name of a function
    :param tree: The abstract syntax tree to walk
    :param old_name: The function name to be changed
    :param new_name: The new name of the old function
    :return: This function modifies the pointer of tree variable so does not return anything
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if node.id == old_name:
                node.id = new_name
        elif isinstance(node, ast.FunctionDef):
            if node.name == old_name:
                node.name = new_name


def update_import_from(tree, modules, name_relations):
    """
    It updates the ImportFrom names of an AST
    :param tree: The abstract syntax tree to walk
    :param modules: A list with the modules imported between the abstract syntax tree
    :param name_relations: A dictionary with the information of how the names are changed
    :return: This function modifies the pointer of tree variable so does not return anything
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in modules:
            for i in range(len(node.names)):
                old_name = node.names[i].name
                node.names[i].name = name_relations[old_name]


def update_function_locations(trees):
    """
    It changes the position of the functions in an abstract syntax tree
    :param trees: A list of abstract syntax trees
    :return: A list of abstract syntax trees with the function position changed
    """
    result = []
    for tree in trees:
        change_global_functions_location(tree)
        change_class_functions_location(tree)
        result.append(tree)
    return result


def change_global_functions_location(tree):
    """
    It changes the position of the definition of the functions
    :param tree: The abstract syntax tree to walk
    :return: This function modifies the pointer of tree variable so does not return anything
    """
    function_locations = []
    for i in range(len(tree.body)):
        if isinstance(tree.body[i], ast.FunctionDef):
            function_locations.append(i)
    if len(function_locations) <= 1:
        return
    for i in range(len(function_locations)):
        j, k = random.sample(function_locations, 2)
        tree.body[j], tree.body[k] = tree.body[k], tree.body[j]


def change_class_functions_location(tree):
    """
    It changes the position of the definition of the functions in every class
    :param tree: The abstract syntax tree to walk
    :return: This function modifies the pointer of tree variable so does not return anything
    """
    for node in ast.walk(tree):
        function_locations = []
        if isinstance(node, ast.ClassDef):
            for i in range(len(node.body)):
                if isinstance(node.body[i], ast.FunctionDef):
                    function_locations.append(i)
            if len(function_locations) <= 1:
                break
            for i in range(len(function_locations)):
                j, k = random.sample(function_locations, 2)
                node.body[j], node.body[k] = node.body[k], node.body[j]


def add_comments(code):
    """
    It adds random one line comments in a python code
    :param code: The code where you want to add the comments
    :return: The code with random comments
    """
    if not code:
        return ""
    lines = code.split(chr(10))
    n = random.randint(len(lines) // 2, len(lines) * 2)
    for _ in range(random.randint(1, n)):
        position = random.randint(1, len(lines) - 1)
        comment = "#" + get_random_name(1, 50)
        spaces = random.randint(0, len(lines[position]) // 2)
        lines.insert(position, " " * spaces + comment)
    return chr(10).join(lines)


def create_final_directory(files):
    """
    It creates the directory of the mutated files
    :param files: A list of files
    :return:
    """
    pathlib.Path("./results").mkdir(exist_ok=True)
    for file in files:
        slash_position = file.rfind(chr(47))
        if slash_position > 0:
            folder = file[:slash_position]
            pathlib.Path("./results/" + folder).mkdir(parents=True, exist_ok=True)


def save_source_code(files, sources):
    """
    It saves the new generated source code
    :param files: A list of files
    :param sources: The code to be saved
    :return:
    """
    for i in range(len(files)):
        with open("./results/" + files[i], "w") as f:
            f.flush()
            f.write(sources[i])


if __name__ == "__main__":
    main()
