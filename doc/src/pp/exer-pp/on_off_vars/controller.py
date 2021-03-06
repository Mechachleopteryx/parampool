import os
from compute import formula as compute_function

from flask import Flask, render_template, request
from model import Formula

# Application object
app = Flask(__name__)

# Path to the web application
@app.route('/', methods=['GET', 'POST'])
def index():
    form = Formula(request.form)
    if request.method == 'POST' and form.validate():

        result = compute(form)

    else:
        result = None

    # Group form into pure numbers and numbers with a boolean
    form_pure_numbers = []
    form_numbers_wbools = []
    for field in form:
        # See if field with name 'include_' + field.name exists
        number_wbool = False
        for field2 in form:
            if field2.name == 'include_' + field.name:
                number_wbool = True
                break
        if number_wbool:
            form_numbers_wbools.append((field, field2))
        elif not field.name.startswith('include_'):
            form_pure_numbers.append(field)

    return render_template("view.html", result=result,
                           form_pure_numbers=form_pure_numbers,
                           form_numbers_wbools=form_numbers_wbools)


def compute(form):
    """
    Generic function for compute_function with arguments
    taken from a form object (wtforms.Form subclass).
    Return the output from the compute_function.
    """
    # Extract arguments to the compute function
    import inspect
    arg_names = inspect.getargspec(compute_function).args

    # Extract values from form
    form_values = [getattr(form, name) for name in arg_names
                   if hasattr(form, name)]

    form_data = [value.data for value in form_values]

    defaults  = inspect.getargspec(compute_function).defaults

    # Make defaults as long as arg_names so we can traverse both with zip
    if defaults:
        defaults = ["none"]*(len(arg_names)-len(defaults)) + list(defaults)
    else:
        defaults = ["none"]*len(arg_names)

    # Convert form data to the right type:
    import numpy
    for i in range(len(form_data)):
        if defaults[i] != "none":
            if isinstance(defaults[i], (str,bool,int,float)):
                pass  # special widgets for these types do the conversion
            elif isinstance(defaults[i], numpy.ndarray):
                form_data[i] = numpy.array(eval(form_data[i]))
            elif defaults[i] is None:
                if form_data[i] == 'None':
                    form_data[i] = None
                else:
                    try:
                        # Try eval if it succeeds...
                        form_data[i] = eval(form_data[i])
                    except:
                        pass # Just keep the text
            else:
                # Use eval to convert to right type (hopefully)
                try:
                    form_data[i] = eval(form_data[i])
                except:
                    print 'Could not convert text %s to %s for argument %s' % (form_data[i], type(defaults[i]), arg_names[i])
                    print 'when calling the compute function...'

    # Run computations
    result = compute_function(*form_data)
    return result

if __name__ == '__main__':
    app.run(debug=True)
