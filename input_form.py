import re
from lxml import etree
import copy

import data_IO


def create_form_xml(tool_name='user_workflow', swift_script='main.swift'):
    form = etree.Element("tool")
    form.set('id', tool_name)
    form.set('name', tool_name)
    command = etree.SubElement(form, "command")
    command.set('interpreter', 'swift')
    command.text = ' ' + swift_script + ' '
    return form


def set_label_from_name(name):
    """
     Creates a label from a name. For example, converts "boxWidthCM" to "Box Width CM"

    :param name: a string that has a parameter name
    :return: label where each word starts with upper case
    """
    # Insert spaces before upper case letters
    label = re.sub(r"(\w)([A-Z])", r"\1 \2", name)
    # Replace "_" with space
    label = label.replace('_', " ")
    label = data_IO.upperfirst(label)
    return label


class Param:
    """
    sets PW input form parameters
    """
    def __init__(self, name, value, param_type, label=None,
                 help_text='Whitespace delimited or range/step (e.g. min:max:step)',
                 section_name=None, width='100'):
        self.name = name
        self.value = value
        self.param_type = param_type

        if label is None:
            label = set_label_from_name(name)
        self.label = label
        self.help_text = help_text
        self.section = section_name
        self.width = width

    def xml_text(self):
        text = "name='{name}' type='{param_type}' value='{value}' label='{label}' " \
               "width='{width}%'".format(**vars(self))
        if self.section is not None:
            text = text + " argument='{section}'".format(**vars(self))
        return text

    def add_to_xml(self, xml_root):
        param_elem = etree.SubElement(xml_root, "param")
        param_elem.set('name', self.name)
        param_elem.set('type', self.param_type)
        param_elem.set('value', '{}'.format(self.value))
        param_elem.set('label', self.label)
        param_elem.set('width', '{}%'.format(self.width))
        if self.section is not None:
            param_elem.set('argument', self.section)
        return param_elem


class Section:
    """
    sets sections in PW input forms
    """
    def __init__(self, name, title=None, expanded=True):
        self.name = name
        if title is None:
            title = set_label_from_name(self.name)
        self.title = title
        self.expanded = expanded
        self.params = []

    def add_param(self, param):
        param.section = self.name
        self.params.append(copy.deepcopy(param))

    def xml_text(self):
        text = "name='{name}' type='section' title='{title}' " \
               "expanded='{expanded}'".format(**vars(self))
        return text

    def add_to_xml(self, xml_root):
        section_elem = etree.SubElement(xml_root, 'section')
        section_elem.set('name', self.name)
        section_elem.set('type', 'section')
        section_elem.set('title', self.title)
        section_elem.set('expanded', '{}'.format(self.expanded))
        return section_elem


class Inputs:
    """
    sets inputs for a PW swift input form
    """
    def __init__(self):
        self.sections = {}
        self.params = []

    def add_param(self, param, section_name=None):
        """
        Add a parameter to the inputs. If a section_name is given, it adds it to an
        existing section with that name or creates a new section and adds the
        parameter to that section. If no section_name is given (section_name=None),
        it sets the section_name to the parameter.section field.
        If both parameter.section and
        section_name are set to None, it adds the parameter to input directly.
        :param param parameter to add to the object
        :param section_name:
        :return:
        """

        if section_name is None:
            # Add param under the inputs object directly, if param doesn't have a section
            if param.section is None:
                self.params.append(copy.deepcopy(param))
                return

            section_name=param.section

        # Add a new empty section, if no section exists with this name already
        if section_name not in self.sections:
            self.add_new_section(section_name)

        param.section = section_name
        self.sections[section_name].params.append(copy.deepcopy(param))

    def add_section(self, section):
        self.sections[section.name] = copy.deepcopy(section)

    def add_new_section(self, name, title=None, expanded=True):
        new_section = Section(name, title, expanded)
        self.add_section(new_section)



