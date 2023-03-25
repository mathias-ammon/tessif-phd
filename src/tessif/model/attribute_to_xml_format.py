def _attribute_xml_format(attribute):
    # A function that corrects the functions in an AES-obj to xml-syntax:
    # frozenset()
    # MinMax()
    # PositiveNegative()
    # math.inf
    # in xml strings in outer nodes are labeled as followed: "'string'" - in contrast to integers: 'integer'
    # input is the raw node_content and returned is the correct formatted content as string
    list_of_functions_to_be_formatted = [
        'frozenset',
        'MinMax',
        'PositiveNegative',
        'OnOff'
    ]
    if attribute == math.inf:
        return '\'+inf\''
    elif attribute == -math.inf:
        return '\'-inf\''
    elif isinstance(attribute, int):
        return str(float(attribute))
    elif isinstance(attribute, float):
        return str(attribute)
    else:
        for item in list_of_functions_to_be_formatted:
            loc = str(attribute).find(item)
            if loc == -1:
                continue
            else:
                if item == list_of_functions_to_be_formatted[0]:  # if attribute holds a frozenset function
                    val_correct = re.findall("frozenset\(\{(.+)\}\)", str(attribute))[0].replace('\'',
                                                                                                 '').split(
                        sep=', ')
                    return str(tuple(val_correct))
                elif item == list_of_functions_to_be_formatted[1]:  # if attribute holds a MinMax function
                    for key in attribute:
                        indicator = str(attribute[key]).find('MinMax')
                        if indicator != -1:
                            val_correct_items = re.findall("MinMax\(min=(.+), max=(.+)\)", str(attribute[key]))[
                                0]
                            val_correct = [None, None]
                            if val_correct_items[0] == 'inf' or val_correct_items[0] == '+inf':
                                val_correct[0] = '+inf'
                            elif val_correct_items[0] == '-inf':
                                val_correct[0] = '-inf'
                            else:
                                try:
                                    float(val_correct_items[0])
                                except:
                                    raise TypeError(
                                        'Arguments of MinMax-function need to be of type integer or \'inf\'')
                                else:
                                    val_correct[0] = float(val_correct_items[0])
                            if val_correct_items[1] == 'inf' or val_correct_items[1] == '+inf':
                                val_correct[1] = '+inf'
                            elif val_correct_items[1] == '-inf':
                                val_correct[1] = '-inf'
                            else:
                                try:
                                    float(val_correct_items[1])
                                except:
                                    raise TypeError(
                                        'Arguments of MinMax-function need to be of type integer or \'inf\'')
                                else:
                                    val_correct[1] = float(val_correct_items[1])
                            attribute[key] = (val_correct[0], val_correct[1])
                        else:
                            continue
                    return str(attribute)
                elif item == list_of_functions_to_be_formatted[
                    2]:  # if attribute holds a PositiveNegative function
                    for key in attribute:
                        indicator = str(attribute[key]).find('PositiveNegative')
                        if indicator != -1:
                            val_correct_items = \
                                re.findall("PositiveNegative\(positive=(.+), negative=(.+)\)", str(attribute[key]))[0]
                            val_correct = [None, None]
                            if val_correct_items[0] == 'inf' or val_correct_items[0] == '+inf':
                                val_correct[0] = '+inf'
                            elif val_correct_items[0] == '-inf':
                                val_correct[0] = '-inf'
                            else:
                                try:
                                    float(val_correct_items[0])
                                except:
                                    raise TypeError(
                                        'Arguments of PositiveNegative-function need to be of type integer or \'inf\'')
                                else:
                                    val_correct[0] = float(val_correct_items[0])
                            if val_correct_items[1] == 'inf' or val_correct_items[1] == '+inf':
                                val_correct[1] = '+inf'
                            elif val_correct_items[1] == '-inf':
                                val_correct[1] = '-inf'
                            else:
                                try:
                                    float(val_correct_items[1])
                                except:
                                    raise TypeError(
                                        'Arguments of PositiveNegative-function need to be of type integer or \'inf\'')
                                else:
                                    val_correct[1] = float(val_correct_items[1])
                            attribute[key] = (val_correct[0], val_correct[1])
                        else:
                            continue
                    return str(attribute)
                elif item == list_of_functions_to_be_formatted[3]:  # if attribute holds a OnOff function
                    val_correct_items = re.findall("OnOff\(on=(.+), off=(.+)\)", str(attribute))[0]
                    val_correct = [None, None]
                    if val_correct_items[0] == 'inf' or val_correct_items[0] == '+inf':
                        val_correct[0] = '+inf'
                    elif val_correct_items[0] == '-inf':
                        val_correct[0] = '-inf'
                    else:
                        try:
                            float(val_correct_items[0])
                        except:
                            raise TypeError(
                                'Arguments of OnOff-function need to be of type integer or \'inf\'')
                        else:
                            val_correct[0] = float(val_correct_items[0])
                    if val_correct_items[1] == 'inf' or val_correct_items[1] == '+inf':
                        val_correct[1] = '+inf'
                    elif val_correct_items[1] == '-inf':
                        val_correct[1] = '-inf'
                    else:
                        try:
                            float(val_correct_items[1])
                        except:
                            raise TypeError(
                                'Arguments of OnOff-function need to be of type integer or \'inf\'')
                        else:
                            val_correct[1] = float(val_correct_items[1])
                    attribute = (val_correct[0], val_correct[1])
                    return str(attribute)
                else:
                    raise AttributeError('a special function was detected but couldn\'t be processed')
        if isinstance(attribute, str):
            return "\'" + 'attribute' + '\''
        else:
            return str(attribute)