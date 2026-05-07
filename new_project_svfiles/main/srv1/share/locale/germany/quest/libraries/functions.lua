-- https://metin2.dev/topic/15905-syreldars-quest-functions/
---@diagnostic disable: undefined-field
--[[
    Description:
        Checks if a `num` number is a valid number.

    Arguments:
        num (number): The number to be checked.
        allow_negative (boolean): Whether negative numbers are allowed.
        allow_decimals (boolean): Whether decimal numbers are allowed.

    Example:
        local result1 = is_valid_number(42, true, true); -- Returns true
        local result2 = is_valid_number(-5, false, true); -- Returns false
        local result3 = is_valid_number(3.14, true, false); -- Returns false

    Returns:
        boolean: True if `num` is a valid number, false otherwise.

    Time complexity: O(1).
    Space complexity: O(1).
]]
is_valid_number = function(num, allow_negative, allow_decimals, allow_zero)
    if (allow_negative == nil) then
        allow_negative = true;
    end -- if

    if (allow_decimals == nil) then
        allow_decimals = false;
    end -- if

    if (allow_zero == nil) then
        allow_zero = true;
    end -- if

    if (not num or type(num) ~= "number") then
        return false;

    elseif (not allow_zero and num == 0) then
        return false;

    elseif (not allow_negative and num < 0) then
        return false;

    elseif (not allow_decimals and num ~= math.floor(num)) then
        return false;

    elseif (({["nan"] = true, ["inf"] = true, ["-inf"] = true})[tostring(num)]) then
        return false;
    end -- if/elseif

    return true;
end -- function

--[[
    Description:
        Checks if a `num` number is an integer.

    Arguments:
        num (number): The number to be checked.

    Example:
        local result1 = is_integer_number(42); -- Returns true
        local result2 = is_integer_number(3.14); -- Returns false

    Returns:
        boolean: True if `num` is an integer, false otherwise.

    Time complexity: O(1).
    Space complexity: O(1).
]]
is_integer_number = function(num)
    return is_valid_number(num, true, false);
end -- function

--[[
    Description:
        Checks if a `num` number is even.

    Arguments:
        num (number): The number to be checked.

    Example:
        local result1 = is_number_even(42); -- Returns true
        local result2 = is_number_even(3); -- Returns false

    Returns:
        boolean: True if `num` is even, false otherwise.

    Time complexity: O(1).
    Space complexity: O(1).
]]
is_number_even = function(num)
    return is_integer_number(num) and math.mod(num, 2) == 0;
end -- function

--[[
    Description:
        Checks if a `num` number is odd.

    Arguments:
        num (number): The number to be checked.

    Example:
        local result1 = is_number_odd(42); -- Returns false
        local result2 = is_number_odd(3); -- Returns true

    Returns:
        boolean: True if `num` is odd, false otherwise.

    Time complexity: O(1).
    Space complexity: O(1).
]]
is_number_odd = function(num)
    return is_integer_number(num) and math.mod(num, 2) ~= 0;
end -- function

--[[
    Description:
        Outputs the factorial of a `num` number.

    Arguments:
        num (number): The number for which to calculate the factorial.

    Example:
        local result1 = factorial(5); -- Returns 120
        local result2 = factorial(0); -- Returns 1

    Returns:
        number: The factorial of `num`.

    Time complexity: O(n).
    Space complexity: O(1).
]]
factorial = function(num)
    local result = 1;

    for i = 2, num do
        result = result * i;
    end -- for

    return result;
end -- function

--[[
    Description:
        Checks if an `element` item is contained inside of a `table_ex` table.

    Arguments:
        table_ex (table): The table to search in.
        element (any): The element to search for in the table.

    Example:
        local table_ex = {1, 2, 3, 4, 5};
        local result1 = table_is_in(table_ex, 3); -- Returns true
        local result2 = table_is_in(table_ex, 6); -- Returns false

    Returns:
        boolean: True if `element` is found in `table_ex`, false otherwise.

    Time complexity: O(n).
    Space complexity: O(1).
]]
table_is_in = function(table_ex, element)
    for _, item in pairs(table_ex) do
        if (item == element) then
            return true;
        end -- if
    end -- for

    return false;
end -- function

--[[
    Description:
        Checks the number of elements contained inside an associative `table_ex` table, or dictionary.

    Arguments:
        table_ex (table): The table to count elements in.

    Example:
        local table_ex = {["a"] = 1, ["b"] = 2, ["c"] = 3}

        local result1 = table_get_count(table_ex) -- Returns 3
        local result2 = table.getn(table_ex) -- Returns 0, see Note.

    Returns:
        number: The number of elements in `table_ex`.

    Time complexity: O(n).
    Space complexity: O(1).

    Note:
        This function is more versatile than `table.getn`.
        While `table.getn` only works for arrays (tables with consecutive integer keys starting at 1),
        `table_get_count` can count elements in both arrays and associative tables with any key types.
        It iterates through the table and counts each key-value pair, providing an accurate count regardless of the table's structure.
]]
table_get_count = function(table_ex)
    if (type(table_ex) ~= "table") then
        return 0;
    end -- if

    local count = 0;
    for _, _ in pairs(table_ex) do
        count = count + 1;
    end -- for

    return count;
end -- function

table_remove_value = function(table_ex, value)
    for index = table_get_count(table_ex), 1, -1 do
        if (table_ex[index] == value) then
            table.remove(table_ex, index);
        end -- if
    end -- for
end -- function

--[[
    Description:
        Checks if a `num` element is not nil and is a number.

    Arguments:
        num (any): The element to check.

    Example:
        local result1 = is_valid_num_field(42); -- Returns true
        local result2 = is_valid_num_field(nil); -- Returns false
        local result3 = is_valid_num_field("not_a_number"); -- Returns false

    Returns:
        boolean: True if `num` is not nil and is a number, false otherwise.

    Time complexity: O(1).
    Space complexity: O(1).
]]
is_valid_num_field = function(num)
    return num and type(num) == "number" and num > 0;
end -- function

--[[
    Description:
        Checks if a `table_ex` element is not nil, is a table, and has at least one element.

    Arguments:
        table_ex (any): The element to check.

    Example:
        local result1 = is_valid_table_field({1, 2, 3}); -- Returns true
        local result2 = is_valid_table_field(nil); -- Returns false
        local result3 = is_valid_table_field({}); -- Returns false

    Returns:
        boolean: True if `table_ex` is not nil, is a table, and has at least one element, false otherwise.

    Time complexity: O(1).
    Space complexity: O(1).
]]
is_valid_table_field = function(table_ex)
    return table_ex and type(table_ex) == "table" and table_get_count(table_ex) > 0;
end -- function

--[[
    Description:
        Checks if a `func` element is not nil and is a function.

    Arguments:
        func (any): The element to check.

    Example:
        local result1 = is_valid_func_field(function() end); -- Returns true
        local result2 = is_valid_func_field(nil); -- Returns false
        local result3 = is_valid_func_field(42); -- Returns false

    Returns:
        boolean: True if `func` is not nil and is a function, false otherwise.

    Time complexity: O(1).
    Space complexity: O(1).
]]
is_valid_func_field = function(func)
    return func and type(func) == "function";
end -- function

--[[
    Description:
        Checks if a `keyword` is a key in a `table_ex` table.

    Arguments:
        table_ex (table): The table to search in.
        keyword (any): The key to search for in the table.

    Example:
        local table_ex = {["cat"] = 1, ["dog"] = 2, ["bird"] = 3};
        local result1 = table_contains_keyword(table_ex, "dog"); -- Returns true
        local result2 = table_contains_keyword(table_ex, "monkey"); -- Returns false

    Returns:
        boolean: True if `keyword` is a key in `table_ex`, false otherwise.

    Time complexity: O(1).
    Space complexity: O(1).
]]
table_contains_keyword = function(table_ex, keyword)
    return table_ex[keyword] ~= nil;
end -- function

--[[
    Description:
        Returns a random element from a `table_ex` table.

    Arguments:
        table_ex (table): The table from which to select a random element.

    Example:
        local table_ex = {1, 2, 3, 4, 5};
        local result1 = table_get_random_item(table_ex); -- Returns a random element, e.g., 2

    Returns:
        any: A random element from `table_ex`.

    Time complexity: O(1).
    Space complexity: O(1).
]]
table_get_random_item = function(table_ex)
    local table_ex_len = table_get_count(table_ex);
    if (table_ex_len == 0) then
        return nil;
    end -- if

    local random_index = math.random(table_ex_len);
    return table_ex[random_index];
end -- function

--[[
    Description:
        Returns a random key from a `table_ex` table that is not in an `except_table`.

    Arguments:
        table_ex (table): The table from which to select a random key.
        except_table (table): The table containing keys to be excluded from selection.

    Example:
        local table_ex = { [30025] = 5, [30026] = 10, [30027] = 15 }
        local result1 = table_get_random_key_except(table_ex, {30025}) -- Returns a random key not in {30025}

    Returns:
        any: A random key from `table_ex` that is not in `except_table`.

    Time complexity: O(k + n), so O(n).
    -> k = number of excluded keys.
    Space complexity: O(1).
]]
table_get_random_key_except = function(table_ex, except_table)
    local excluded_keys = {};
    for _, key in pairs(except_table) do
        excluded_keys[key] = true;
    end -- for

    local accepted_keys = {};
    for key, _ in pairs(table_ex) do
        if (not excluded_keys[key]) then
            table.insert(accepted_keys, key);
        end -- if
    end -- for

    return table_get_random_item(accepted_keys);
end -- function

--[[
    Description:
        Returns a random element from a `table_ex` table that is not in an `except_table`.

    Arguments:
        table_ex (table): The table from which to select a random element.
        except_table (table): The table containing elements to be excluded from selection.

    Example:
        local table_ex = {1, 2, 3, 4, 5};
        local result1 = table_get_random_item_except(table_ex, {4, 1}); -- Returns a random element not in {4, 1}

    Returns:
        any: A random element from `table_ex` that is not in `except_table`.

    Time complexity: O(k + n), so O(n).
    -> k = number of excluded values.
    Space complexity: O(1).
]]
table_get_random_item_except = function(table_ex, except_table)
    local excluded_values = {};
    for _, value in pairs(except_table) do
        excluded_values[value] = true;
    end -- for

    local accepted_items = {};
    for _, value in pairs(table_ex) do
        if (not excluded_values[value]) then
            table.insert(accepted_items, value);
        end -- if
    end -- for

    return table_get_random_item(accepted_items);
end -- function

--[[
    Description:
        Returns a random number within a specified range that is not in an `except_table`.

    Arguments:
        range_min (number): The minimum value of the desired range (inclusive).
        range_max (number): The maximum value of the desired range (inclusive).
        except_table (table): A table containing values to be excluded from the random selection.

    Example:
        local result1 = get_random_number_within_except(1, 10, {4, 7}); -- Returns a random number between 1 and 10, excluding 4 and 7

    Returns:
        number: A random number within the specified range that is not in `except_table`.

    Time complexity: O(k + n), so O(n).
    -> k = number of excluded values.
    Space complexity: O(1).
]]
get_random_number_within_except = function(range_min, range_max, except_table)
    local excluded_values = {};
    for _, value in pairs(except_table) do
        excluded_values[value] = true;
    end -- for

    local random_num = math.random(range_min, range_max);
    while excluded_values[random_num] do
        random_num = math.random(range_min, range_max);
    end -- while

    return random_num;
end -- function

--[[
    Description:
        Returns the index of an `element` in a `table_ex` table, or nil if not found.

    Arguments:
        table_ex (table): The table to search in.
        element (any): The element to search for in the table.

    Example:
        local table_ex = {5, 7, 9};
        local result1 = table_get_element_index(table_ex, 5); -- Returns 1
        local result2 = table_get_element_index(table_ex, 11); -- Returns nil

    Returns:
        number: The index of `element` in `table_ex`, or nil if not found.

    Time complexity: O(n).
    Space complexity: O(1).
]]
table_get_element_index = function(table_ex, element)
    for index, value in pairs(table_ex) do
        if (value == element) then
            return index;
        end -- if
    end -- for

    return nil;
end -- function

--[[
    Description:
        Extracts and returns all keys from a given table `table_ex` in an array format.

    Arguments:
        table_ex (table): The table from which to retrieve keys.

    Example:
        local example_table = {a = 1, b = 2, c = 3};
        local keys = table_get_keys(example_table); -- Returns {"a", "b", "c"}

    Returns:
        table: An array containing all keys from `table_ex`.

    Time complexity: O(n) - where n is the number of elements in `table_ex`.
    Space complexity: O(n) - requires additional space to store the keys array.
]]
table_get_keys = function(table_ex)
    local keys = {};
    for key, _ in pairs(table_ex) do
        table.insert(keys, key);
    end -- for

    return keys;
end -- function

--[[
    Description:
        Checks if any subarray in a `array_of_arrays` table contains a `keyword`.

    Arguments:
        array_of_arrays (table): The table of subarrays to search in.
        keyword (any): The keyword to search for in the subarrays.

    Example:
        local array_of_arrays = {
            {["bird"] = "chirp"},
            {["cat"] = "meow"},
            {["dog"] = "whoof"}
        };
        local result1 = table_is_any_subarray_containing_keyword(array_of_arrays, "cat"); -- Returns true
        local result2 = table_is_any_subarray_containing_keyword(array_of_arrays, "cow"); -- Returns false

    Returns:
        boolean: True if any subarray in `array_of_arrays` contains `keyword`, false otherwise.

    Time complexity: O(n).
    Space complexity: O(1).
]]
table_is_any_subarray_containing_keyword = function(array_of_arrays, keyword)
    if (array_of_arrays == nil or keyword == nil) then
        return false;
    end -- if

    for _, subarray in ipairs(array_of_arrays) do
        if (subarray ~= nil and type(subarray) == "table") then
            for _, value in ipairs(subarray) do
                if (value == keyword) then
                    return true
                end -- if
            end -- for
        end -- if
    end -- for

    return false;
end -- function

--[[
    Description:
        Returns the index of the subarray containing a `keyword` in a `table_ex` table, or nil if not found.

    Arguments:
        table_ex (table): The table of subarrays to search in.
        keyword (any): The keyword to search for in the subarrays.

    Example:
        local table_ex = {
            {["bird"] = "chirp"},
            {["cat"] = "meow"},
            {["dog"] = "whoof"}
        };
        local result1 = table_get_subarray_keyword_index(table_ex, "dog"); -- Returns 3
        local result2 = table_get_subarray_keyword_index(table_ex, "worm"); -- Returns nil

    Returns:
        number: The index of the subarray containing `keyword`, or nil if not found.

    Time complexity: O(n).
    Space complexity: O(1).
]]
table_get_subarray_keyword_index = function(table_ex, keyword)
    for index, subarray in ipairs(table_ex) do
        if (subarray[keyword]) then
            return index;
        end -- if
    end -- for

    return nil;
end -- function

--[[
    Description:
        Shuffles the elements in a `table_ex` table and returns a shuffled version.

    Arguments:
        table_ex (table): The table to shuffle.

    Example:
        local table_ex = {1, 2, 3, 4, 5};
        local result1 = table_shuffle(table_ex); -- Returns a shuffled table

    Returns:
        table: The shuffled version of `table_ex`.

    Time complexity: O(n).
    Space complexity: O(n).
]]
table_shuffle = function(table_ex)
    local shuffled_table = {};
    for i = 1, table_get_count(table_ex) do
        shuffled_table[i] = table_ex[i];
    end -- for

    local rand = 0;
    for i = table_get_count(shuffled_table), 1, -1 do
        rand = math.random(i);
        shuffled_table[i], shuffled_table[rand] = shuffled_table[rand], shuffled_table[i];
    end -- for

    return shuffled_table;
end -- function

--[[
    Description:
        Reorders elements in `target_table` based on the shuffling of `original_table` reflected in `shuffled_table`.

    Arguments:
        original_table (table): The original unshuffled table.
        shuffled_table (table): The shuffled version of `original`.
        target_table (table): The table to reorder following the pattern of `shuffled`.

    Example:
        local original = {1, 2, 3, 4, 5};
        local shuffled = {3, 1, 4, 5, 2};
        local target = {'a', 'b', 'c', 'd', 'e'};
        local result = mirror_shuffle(original, shuffled, target);
        -- result is {'c', 'a', 'd', 'e', 'b'}

    Returns:
        table: A new table with elements of `target_table` reordered to mirror the shuffle from `original_table` to `shuffled_table`.

    Time complexity: O(n).
    Space complexity: O(n).
]]
mirror_shuffle = function(original_table, shuffled_table, target_table)
    local map_table = {};
    for index, value in ipairs(original_table) do
        map_table[value] = index;
    end -- for

    local new_order_table = {};
    for _, value in ipairs(shuffled_table) do
        new_order_table[table_get_count(new_order_table) + 1] = target_table[map_table[value]];
    end -- for

    return new_order_table;
end -- function

--[[
    Description:
        Counts the number of digits in a given integer using logarithmic calculation, compatible with Lua 5.0.

    Arguments:
        num (integer): The number whose digits are to be counted.

    Example:
        local digits = count_digits(1234); -- Returns 4, as there are 4 digits in 1234

    Returns:
        integer: The number of digits in the given number.

    Time complexity: O(1), as logarithmic calculation is a constant time operation.
    Space complexity: O(1), as only a single calculation is performed.
]]
count_digits = function(num)
    if (num == 0) then
        return 1;
    end -- if

    num = math.abs(num);
    return math.floor(math.log(num) / math.log(10) + 1);
end -- function

--[[
    Description:
        Retrieves the nth digit of a given number.

    Arguments:
        num (integer): The number from which the digit is to be extracted.
        index (integer): The position of the digit to retrieve, where 1 is the first digit.

    Example:
        local digit = get_nth_digit(1234, 3); -- Returns 3, as the third digit of 1234 is 3

    Returns:
        integer: The nth digit of the given number. Returns nil if `n` is outside the range of the number's length.

    Time complexity: O(1), as string conversion and digit retrieval are constant time operations.
    Space complexity: O(n), where n is the number of digits in the number, due to the string conversion.
]]
get_nth_digit = function(num, index)
    local total_digits = count_digits(num);
    if (index < 1 or index > total_digits) then
        return -1;
    end -- if

    local str = tostring(num);
    return tonumber(string.sub(str, index, index));
end -- function

--[[
    Description:
        Generates an array containing numbers from `min` up to `max`.
        If only one argument is provided, it’s treated as `max` and `min` defaults to 1.

    Arguments:
        min (integer, optional): The lower bound of the number range. Defaults to 1 if omitted.
        max (integer): The upper bound of the number range.

    Example:
        local result1 = generate_num_array(4)
        -- Returns {1, 2, 3, 4}

        local result2 = generate_num_array(3, 6)
        -- Returns {3, 4, 5, 6}

    Returns:
        table: An array containing numbers from `min` to `max`.

    Time complexity: O(n), where n = max - min + 1.
    Space complexity: O(n), where n = max - min + 1.
]]
generate_num_array = function(min, max)
    local temp_min, temp_max = 1, min; -- if only one argument is given, treat it as max.
    if (max ~= nil) then
        temp_min, temp_max = min, max;
    end -- if

    local num_array = {};
    for num = temp_min, temp_max do
        table.insert(num_array, num);
    end -- for

    return num_array;
end -- function

--[[
    Description:
        Converts time values between units.

    Arguments:
        value (number): The numerical value to convert.
        unit (string): The unit of time ("min", "hour", "day", "week", "month_28_days", "month_30_days", "month_31_days").

    Example:
        local result1 = time_to_sec(5, "min"); -- Returns the number of seconds contained in 5 minutes
        local result2 = time_hour_to_sec(2); -- Returns the number of seconds contained in 2 hours

    Returns:
        number: The number of seconds corresponding to 'value' in the given 'unit'.

    Time complexity: O(1).
    Space complexity: O(1).
]]
time_to_sec = function(value, unit)
    local units = {
        min = 60,
        hour = 3600,
        day = 86400,
        week = 604800,
        month_28_days = 2419200,
        month_30_days = 2592000,
        month_31_days = 2678400
    };

    return units[unit] * value;
end -- function

--[[
    Returns:
        The number of seconds contained in a number of minutes given by 'value'.
]]
time_min_to_sec = function(value)
    return time_to_sec(value, "min")
end -- function

--[[
    Returns:
        The number of seconds contained in a number of hours given by 'value'.
]]
time_hour_to_sec = function(value)
    return time_to_sec(value, "hour")
end -- function

--[[
    Returns:
        The number of seconds contained in a number of days given by 'value'.
]]
time_day_to_sec = function(value)
    return time_to_sec(value, "day")
end -- function

--[[
    Returns:
        The number of seconds contained in a number of weeks given by 'value'.
]]
time_week_to_sec = function(value)
    return time_to_sec(value, "week")
end -- function

--[[
    Returns:
        The number of seconds contained in a number of 28-day months given by 'value'.
]]
time_month_to_sec_28_days = function(value)
    return time_to_sec(value, "month_28_days")
end -- function

--[[
    Returns:
        The number of seconds contained in a number of 30-day months given by 'value'.
]]
time_month_to_sec_30_days = function(value)
    return time_to_sec(value, "month_30_days")
end -- function

--[[
    Returns:
        The number of seconds contained in a number of 31-day months given by 'value'.
]]
time_month_to_sec_31_days = function(value)
    return time_to_sec(value, "month_31_days")
end -- function

--[[
    Description:
        Formats a numerical `amount` with a dot as a thousands separator for better readability.
        Supports negative number and floating-point numbers (substitutes the dot for them with a comma);

    Arguments:
        amount (number): The number to be formatted.

    Example:
        local result1 = get_gold_format(1000); -- Returns "1.000"
        local result2 = get_gold_format(-12345.67); -- Returns "-12.345,67"

    Returns:
        string: The formatted string version of `amount`.

    Time complexity: O(1).
    Space complexity: O(1).
]]
get_gold_format = function(amount)
    local str = tostring(amount);
    local int_part = str;
    local fract_part = "";

    local dot_position = string.find(str, "%.");
    if (dot_position) then
        int_part = string.sub(str, 1, dot_position - 1);
        fract_part = string.sub(str, dot_position + 1);
    end -- if


    local formatted_int = int_part;
    local k;
    repeat
        formatted_int, k = string.gsub(formatted_int, "^(-?%d+)(%d%d%d)", '%1.%2');
    until (k == 0)


    if (fract_part ~= "") then
        fract_part = "," .. fract_part;
    end -- if

    return formatted_int .. fract_part;
end -- function

--[[
    Description:
        Returns a string representing the total time in either the "Days, Hours, Minutes and Seconds" or "d:h:m:s" format.

    Arguments:
        sec (number): The total amount of seconds.
        format_type (string): Optional parameter, either "verbose" or "clock".
        simplify (boolean): Optional parameter, valid only if format_type is "clock". If true, the labels ("d", "h", "m", "s") will be omitted.

    Example:
        get_time_format(52165786, "verbose") -- Returns "603 days, 18 hours, 29 minutes and 46 seconds"
        get_time_format(52165786, "clock") -- Returns "603d:18h:29m:46s"
        get_time_format(52165786, "clock", true) -- Returns "603:18:29:46"

    Returns:
        string: A string representing the total time.

    Time complexity: O(1).
    Space complexity: O(1).
]]
local lang_time_words = {
    ["day"] = {"day", "days"},
    ["hour"] = {"hour", "hours"},
    ["minute"] = {"minute", "minutes"},
    ["second"] = {"second", "seconds"}
};

get_time_format = function(sec, format_type, simplify)
    format_type = format_type or "verbose";
    simplify = simplify or false;

    local days = math.floor(sec / time_day_to_sec(1));
    local hours = math.floor(math.mod(sec, time_day_to_sec(1)) / time_hour_to_sec(1));
    local minutes = math.floor(math.mod(sec, time_hour_to_sec(1)) / time_min_to_sec(1));
    local seconds = math.mod(sec, time_min_to_sec(1));

    if (format_type == "verbose") then
        local parts = {};
        local function add_part(quantity, words)
            if (quantity > 0) then
                table.insert(parts, string.format("%d %s", quantity, words[quantity > 1 and 2 or 1]));
            end -- if
        end -- function

        add_part(days, lang_time_words["day"]);
        add_part(hours, lang_time_words["hour"]);
        add_part(minutes, lang_time_words["minute"]);
        add_part(seconds, lang_time_words["second"]);

        local parts_num = table_get_count(parts);
        if (parts_num > 1) then
            parts[parts_num - 1] = string.format("%s and %s", parts[parts_num - 1], parts[parts_num]);
            table.remove(parts);
        end -- if

        return table.concat(parts, ", ");

    elseif (format_type == "clock") then
        local parts = {};

        if (days > 0) then
            table.insert(parts, string.format("%dd", days));
        end -- if

        if (hours > 0 or table.getn(parts) > 0) then
            table.insert(parts, string.format("%02dh", hours));
        end -- if

        if (minutes > 0 or table.getn(parts) > 0) then
            table.insert(parts, string.format("%02dm", minutes));
        end -- if

        table.insert(parts, string.format("%02ds", seconds));

        if (simplify) then
            for i = 1, table.getn(parts) do
                parts[i] = string.gsub(parts[i], "%a", "");
            end -- for
        end -- if

        return table.concat(parts, ":");
    end -- if/elseif
end -- function

--[[
    Description:
        Returns the number of seconds remaining until a specified time of day.

    Arguments:
        time_ex (string): The target time of day in "HH:MM" 24-hour format.

    Example:
        time_remaining_until("23:00") -- Returns the number of seconds remaining until 11 PM.

    Returns:
        number: The number of seconds remaining.

    Time complexity: O(1).
    Space complexity: O(1).
]]
time_remaining_until = function(time_ex)
    local SEC_MIN = time_min_to_sec(1);
    local SEC_HOUR = time_hour_to_sec(1);
    local SEC_DAY = time_day_to_sec(1);

    local target_h, target_m;
    string.gsub(time_ex, "^(%d%d):(%d%d)", function(h, m)
        target_h = tonumber(h);
        target_m = tonumber(m);
    end); -- function

    local tm = os.date("*t");
    local now_secs = tm.hour*SEC_HOUR + tm.min*SEC_MIN;
    local target_secs = target_h*SEC_HOUR + target_m*SEC_MIN;

    local delta = target_secs - now_secs;
    if (delta < 0) then
        delta = delta + SEC_DAY;
    end -- if

    return delta;
end -- function

--[[
    Description:
        Calculates the future time based on the current system time and an additional number of seconds.
        The function retrieves the current hour and minute from the system, adds the specified seconds,
        and returns the resulting time in a 24-hour format.

    Arguments:
        sec (number): The number of seconds to add to the current system time.

    Example:
        get_time_after_seconds(600) -- If the current time is 18:00:00, this returns "18:10:00"

    Returns:
        string: A string representing the future time in "HH:MM:SS" format, based on the current system time
        and the added seconds.

    Notes:
        The function handles the day transition, so if the time addition crosses midnight, the hour is adjusted accordingly.
        The function assumes that the system time is accurate and correctly set.

    Time complexity: O(1).
    Space complexity: O(1).
]]
get_time_after_seconds = function(sec)
    local SEC_MIN = time_min_to_sec(1);
    local SEC_HOUR = time_hour_to_sec(1);

    local tm = os.date("*t");
    local total_seconds = tm.sec + sec;
    local carry_minutes = math.floor(total_seconds / SEC_MIN);
    local new_seconds = math.mod(total_seconds, SEC_MIN);

    local total_minutes = tm.min + carry_minutes;
    local carry_hours = math.floor(total_minutes / SEC_MIN);
    local new_minute = math.mod(total_minutes, SEC_MIN);

    local new_hour = tm.hour + carry_hours;
    local hours_in_a_day = 24;
    if (new_hour >= hours_in_a_day) then
        new_hour = new_hour - hours_in_a_day;
    end -- if

    return string.format("%02d:%02d:%02d", new_hour, new_minute, new_seconds);
end -- function

--[[
    Description:
        Returns a string representing the Roman numeral equivalent of a given integer.

    Arguments:
        int (number): The integer to be converted to a Roman numeral.

    Example:
        int_to_roman_str(23) -- Returns "XXIII"

    Returns:
        string: The Roman numeral representation.

    Time complexity: O(1).
    Space complexity: O(1).
]]
int_to_roman_str = function(int)
    if (not is_valid_number(int, false, false)) then
        return "0";
    end -- if

    local roman_numerals = {
        {1000, "M"}, {900, "CM"}, {500, "D"}, {400, "CD"},
        {100, "C"},  {90, "XC"},  {50, "L"},  {40, "XL"},
        {10, "X"},   {9, "IX"},   {5, "V"},   {4, "IV"},
        {1, "I"}
    };

    local ret = "";
    local temp_int = int;
    for i = 1, table_get_count(roman_numerals) do
        while (temp_int >= roman_numerals[i][1]) do
            ret = ret .. roman_numerals[i][2];
            temp_int = temp_int - roman_numerals[i][1];
        end -- while
    end -- for

    return ret;
end -- function

--[[
    Description:
        Returns a boolean representing whether a given string is a valid Roman numeral.

    Arguments:
        str (string): The string to be checked.

    Example:
        is_valid_roman_str("XXIII") -- Returns true
        is_valid_roman_str("XXMIII") -- Returns false

    Returns:
        boolean: True if the string is a valid Roman numeral, false otherwise.

    Time complexity: O(n), where n is the length of the string.
    Space complexity: O(1).
]]
is_valid_roman_str = function(str)
    if (not str or str == "") then
        return false;
    end -- if

    local valid_romans = {
        ["I"] = 1,   ["V"] = 5,
        ["X"] = 10,  ["L"] = 50,
        ["C"] = 100, ["D"] = 500,
        ["M"] = 1000
    };

    local cur_char = "";
    for i = 1, string.len(str) do
        cur_char = string.sub(str, i, i);
        if (not valid_romans[cur_char]) then
            return false;
        end -- if
    end -- for

    return true;
end -- function

--[[
    Description:
        Returns an integer equivalent of a given Roman numeral string.

    Arguments:
        str (string): The Roman numeral string to be converted.

    Example:
        roman_str_to_int("XXIII") -- Returns 23
        roman_str_to_int("XXMIII") -- Returns 0, because "XXMIII" is not a valid Roman numeral

    Returns:
        number: The integer equivalent of the Roman numeral string.

    Time complexity: O(n), where n is the length of the string.
    Space complexity: O(1).
]]
roman_str_to_int = function(str)
    if (not is_valid_roman_str(str)) then
        return 0;
    end -- if

    local valid_romans = {
        ["I"] = 1,   ["V"] = 5,
        ["X"] = 10,  ["L"] = 50,
        ["C"] = 100, ["D"] = 500,
        ["M"] = 1000
    };

    local ret = 0;
    local prev_val, cur_val = 0, 0;

    for i = string.len(str), 1, -1 do
        cur_val = valid_romans[string.sub(str, i, i)];
        if (cur_val < prev_val) then
            ret = ret - cur_val;
        else
            ret = ret + cur_val;
        end -- if/else

        prev_val = cur_val;
    end -- for

    return ret;
end -- function

--[[
    Description:
        Returns a decimal number converted from a binary number.

    Arguments:
        bin (number): The binary number to be converted.

    Example:
        bin_to_num(1011) -- Returns 11

    Returns:
        number: The decimal number equivalent to the binary input.

    Time complexity: O(n), where n is the number of digits in the binary number.
    Space complexity: O(1).
]]
bin_to_num = function(bin)
    local decimal = 0;
    local multiplier = 1;

    while (bin > 0) do
        local remainder = math.mod(bin, 10);
        bin = math.floor(bin / 10);
        decimal = decimal + remainder * multiplier;
        multiplier = multiplier * 2;
    end -- while

    return decimal;
end -- function

--[[
    Description:
        Returns a binary string converted from a decimal number.

    Arguments:
        num (number): The decimal number to be converted.

    Example:
        num_to_bin(11) -- Returns "1011"

    Returns:
        string: The binary representation of the decimal input.

    Time complexity: O(log n), where n is the decimal number.
    Space complexity: O(log n), because the binary representation length is proportional to the logarithm of the number.
]]
num_to_bin = function(num)
    local binary = "";
    local temp_num = num;

    while (temp_num > 0) do
        binary = math.mod(temp_num, 2) .. binary;
        temp_num = math.floor(temp_num / 2);
    end -- while

    return binary;
end -- function

--[[
    Description:
        Returns a number converted from a character based on ASCII values.

    Arguments:
        c (char): The character to be converted.

    Example:
        char_to_num("A") -- Returns 10

    Returns:
        number: The numeric value of the character based on ASCII values.

    Time complexity: O(1).
    Space complexity: O(1).
]]
char_to_num = function(c)
    local ascii = string.byte(c);
    if (ascii >= 48 and ascii <= 57) then -- 0-9
        return ascii - 48;
    elseif (ascii >= 65 and ascii <= 90) then -- A-Z
        return ascii - 65 + 10;
    elseif (ascii >= 97 and ascii <= 122) then -- a-z
        return ascii - 97 + 36;
    end -- if/elseif

    return -1;
end -- function

--[[
    Description:
        Returns a character converted from a number based on ASCII values.

    Arguments:
        n (number): The number to be converted.

    Example:
        num_to_char(10) -- Returns "A"

    Returns:
        char: The character corresponding to the numeric value based on ASCII values.

    Time complexity: O(1).
    Space complexity: O(1).
]]
num_to_char = function(n)
    if (n >= 0 and n <= 9) then -- 0-9
        return string.char(n + 48);
    elseif (n >= 10 and n <= 35) then -- A-Z
        return string.char(n - 10 + 65);
    elseif (n >= 36 and n <= 61) then -- a-z
        return string.char(n - 36 + 97);
    end -- if/elseif

    return "";
end -- function

--[[
    Description:
        Returns an array of ASCII values representing each character in the 'str' string.

    Arguments:
        str (string): The string to be converted into an array of ASCII values.

    Example:
        string_to_ascii_array("hello") -- Returns {104, 101, 108, 108, 111}

    Returns:
        table: An array of ASCII values.

    Time complexity: O(n), where n is the length of the string.
    Space complexity: O(n), where n is the length of the string.
]]
string_to_ascii_array = function(str)
    local array = {};
    local str_len = string.len(str);
    for i = 1, str_len do
        array[i] = string.byte(str, i);
    end -- for

    return array;
end -- function

--[[
    Description:
        Returns a string converted from an array of ASCII values.

    Arguments:
        array (table): The array of ASCII values to be converted into a string.

    Example:
        ascii_array_to_string({104, 101, 108, 108, 111}) -- Returns "hello"

    Returns:
        string: The string representation of the ASCII values.

    Time complexity: O(n), where n is the length of the array.
    Space complexity: O(n), where n is the length of the array.
]]
ascii_array_to_string = function(array)
    local str = "";
    local array_len = table_get_count(array);
    for i = 1, array_len do
        str = str .. string.char(array[i]);
    end -- for

    return str;
end -- function

--[[
    Description:
        Returns a string with a random number of characters removed from each word, while ensuring
        that no word is completely removed. The number of characters removed is random between 2 and 3.

    Arguments:
        str (string): The input string containing words separated by spaces.

    Example:
        random_fragment("This is a test string.") -- Returns a string with random character removals.

    Returns:
        string: A new string with some characters removed from each word.

    Time complexity: O(n + m * w), where n is the length of the string, m is the number of words,
                    and w is the average word length.
    Space complexity: O(n), where n is the length of the string.
]]
function random_fragment(str)
    local words = {};
    local spaces = {};
    local pos = 1;
    local string_len = string.len(str);

    while (pos <= string_len) do
        local space_start, space_end = string.find(str, "%s*", pos);
        local word_start, word_end = string.find(str, "%S+", space_end + 1);
        if (not word_start) then
            break;
        end -- if

---@diagnostic disable-next-line: param-type-mismatch
        table.insert(spaces, string.sub(str, space_start, space_end));
        table.insert(words, string.sub(str, word_start, word_end));
        pos = word_end + 1;
    end -- while

    local total_removals = math.random(2, 3); -- Remove between 3 and 4 characters (not spaces)
    local removals = {};
    local words_size = table.getn(words) -- Cache size of words

    for i = 1, words_size do
        removals[i] = 0;
    end -- for

    for i = 1, words_size do
        if (total_removals > 0) then
            removals[i] = 1;
            total_removals = total_removals - 1;
        end -- if
    end -- for

    while (total_removals > 0) do
        local idx = math.random(words_size);
        local word_len = string.len(words[idx]);

        if (word_len > removals[idx]) then
            local max_removal = math.min(word_len - removals[idx] - 1, total_removals);
            removals[idx] = removals[idx] + max_removal;
            total_removals = total_removals - max_removal;
        end -- if
    end -- while

    local result = spaces[1] or "";
    for i = 1, words_size do
        local word = words[i];
        local removal_count = removals[i];

        if (removal_count > 0) then
            local ascii_values = string_to_ascii_array(word);

            for _ = 1, removal_count do
                local rand_idx = math.random(table.getn(ascii_values));
                table.remove(ascii_values, rand_idx);
            end -- for

            word = ascii_array_to_string(ascii_values);
        end -- if

        result = result .. word;
        if (spaces[i + 1]) then
            result = result .. spaces[i + 1];
        end -- if
    end -- for

    return result;
end -- function

--[[
    Description:
        Converts random characters in the input string to either uppercase or lowercase.

    Arguments:
        str (string): The input string to modify.

    Example:
        random_case("Hello World") -- Returns a string with random characters in uppercase or lowercase.

    Returns:
        string: The modified string with random characters changed to uppercase or lowercase.

    Time complexity: O(n), where n is the length of the string.
    Space complexity: O(n), where n is the length of the string.
]]
random_case = function(str)
    local result = {}
    local string_len = string.len(str)
    for i = 1, string_len do
        table.insert(result, string.sub(str, i, i))
    end -- for

    for i = 1, string_len do
        if (math.random(100) <= 33) then
            if (math.random(2) == 1) then
                result[i] = string.upper(result[i]);
            else
                result[i] = string.lower(result[i]);
            end -- if/else
        end -- if
    end -- for

    return table.concat(result);
end -- function

--[[
    Description:
        Returns a string that represents the ID of the level.

    Arguments:
        level (number): The numeric level to be converted into an ID.

    Example:
        skill_level_to_id(35) -- Returns "G6"

    Returns:
        string: The level ID.

    Time complexity: O(1)
    Space complexity: O(1)

    Dependencies:
        https://metin2.dev/topic/29230-syreldars-useful-globals
]]
skill_level_to_id = function(level)
    if (level == SKILL_LEVEL.PERFECT_MASTER) then
        return "P";
    end -- if

    local map = {
        {["step"] = SKILL_LEVEL.GRAND_MASTER, ["format"] = "G%d"},
        {["step"] = SKILL_LEVEL.MASTER,       ["format"] = "M%d"}
    };

    for _, skill_data in ipairs(map) do
        local step, format = skill_data["step"], skill_data["format"];
        if (level >= step) then
            return string.format(format, level - step + 1);
        end -- if
    end -- for

    return tostring(level);
end -- function

--[[
    Description:
        Returns a number that represents the level of the given ID.

    Arguments:
        id (string): The ID to be converted into a numeric level.

    Example:
        skill_id_to_level("G6") -- Returns 35

    Returns:
        number: The numeric level.

    Time complexity: O(1)
    Space complexity: O(1)

    Dependencies:
        https://metin2.dev/topic/29230-syreldars-useful-globals
]]
skill_id_to_level = function(id)
    if (id == "P") then
        return SKILL_LEVEL.PERFECT_MASTER;
    end -- if

    -- For other ids, proceed with the original logic
    local prefix, num_str = string.match(id, "([GMP]?)(%d+)");
    local num = tonumber(num_str);
    local prefix_map = {
        ["G"] = SKILL_LEVEL.GRAND_MASTER - 1,
        ["M"] = SKILL_LEVEL.MASTER - 1
    };

    return (prefix_map[prefix] or 0) + num;
end -- function

item_has_upgrade_level = function(item_vnum)
    local item_name = item_name(item_vnum);
    local pattern = "%+%d+$";
    local match_start = string.find(item_name, pattern);
    return match_start ~= nil;
end -- function

get_item_name_or_upgrade_level = function(item_vnum)
    local item_name = item_name(item_vnum);
    local pattern = "(.-)%s*(%+[%d]+)$";
    local start, _, name, level = string.find(item_name, pattern);

    if (not start) then
        name = item_name;
        level = "No upgrade";
    end -- if

    return name, level;
end -- function

set_dungeon_leader_name = function(name)
    local array = string_to_ascii_array(name);
    for index, value in ipairs(array) do
        d.setf(string.format("leader_name%d", index), value);
    end -- for
end -- function

get_dungeon_leader_name = function()
    local table_ex, i = {}, 1;
    local flag = d.getf(string.format("leader_name%d", i));

    while (flag and flag ~= 0) do
        table_ex[table_get_count(table_ex) + 1] = flag;
        i = i + 1;
        flag = d.getf(string.format("leader_name%d", i));
    end -- while

    return ascii_array_to_string(table_ex);
end -- function

--[[
    Executes:
        A clear of the currently active set regen, if present.
        Kills all currently alive dungeon monsters.
        Some monsters revive once, thus a second d.kill_all() call is needed.
]]
clear_dungeon = function()
    d.clear_regen();
    d.kill_all();
    d.kill_all(); -- Needed for resurrecting monsters.
end -- function

upper_notice = function(dungeon, str)
    local notice_function;

    if (dungeon) then
        notice_function = d.big_notice or d.notice;
    else
        notice_function = big_notice or notice;
    end -- if/else

    return notice_function(str)
end -- function

is_same_pc_race = function(race1, race2)
    return (table_is_in(PC_RACE_LIST, race1) and table_is_in(PC_RACE_LIST, race2))
        or (table_is_in(PC2_RACE_LIST, race1) and table_is_in(PC2_RACE_LIST, race2));
end -- function

--[[
    Returns:
        The pids of all the online party members in the same instance (online and in the same channel, core and map).
]]
party_get_member_pids = function()
    return {party.get_member_pids()};
end -- function

--[[
    Returns:
        The number of members in the party that are in the same instance (online and in the same channel, core and map).
]]
party_get_member_count = function()
    return table_get_count(party_get_member_pids());
end -- function

--[[
    Returns:
        The index of the first dungeon instance of the map which index is 'map_index'.

    Dependencies:
        https://metin2.dev/topic/29230-syreldars-useful-globals
]]
ToDungeonIndex = function(map_index)
    return map_index * DUNGEON_DATA.START_INDEX;
end -- function

--[[
    Returns:
        The normalized index of the map which index is 'map_index'.

    Dependencies:
        https://metin2.dev/topic/29230-syreldars-useful-globals
]]
ToNormalIndex = function(map_index)
    local start_index = DUNGEON_DATA.START_INDEX;
    return map_index >= start_index and math.floor(map_index / start_index) or map_index;
end -- function

--[[
    Returns:
        true, if the player is in the dungeon instance of the map which index is 'map_index',
        else, false.
]]
InDungeon = function(map_index)
    local pc_index = pc.get_map_index();
    return
        pc.in_dungeon() and
        pc_index >= ToDungeonIndex(map_index) and
        pc_index < ToDungeonIndex(map_index+1);
end -- function

--[[
    Returns:
        An array containing 2 subarrays:
        - The first subarray, vnum_list, contains the vnums of the skills;
        - The second subarray, name_list, contains the names of the skills;

    Dependencies:
        https://metin2.dev/topic/29230-syreldars-useful-globals
]]
BuildSkillList2 = function(job, group, min_level, max_level)
    if (not job) then
        job = pc.get_job();
    end -- if

    if (not group or pc.get_skill_group() == SKILL_GROUP.NONE) then
        group = SKILL_GROUP.FIRST_SPEC;
    end -- if

    if (not min_level) then
        min_level = SKILL_LEVEL.BASE;
    end -- if

    if (not max_level) then
        max_level = SKILL_LEVEL.PERFECT_MASTER-1;
    end -- if

    local skill_level = 0;
    local skill_list = ACTIVE_SKILL_LIST[job][group];

    local vnum_list, name_list = {}, {};
    for _, skill_vnum in ipairs(skill_list) do
        skill_level = pc.get_skill_level(skill_vnum);
        if (skill_level >= min_level and skill_level <= max_level) then
            table.insert(vnum_list, skill_vnum);
            table.insert(name_list, SKILL_NAME_TABLE[skill_vnum]);
        end -- if
    end -- for

    return {vnum_list, name_list};
end -- function

--[[
    Converts RGB to HSL
    Returns: h, s, l
]]
function rgb_to_hsl(r, g, b)
    r, g, b = r / 255, g / 255, b / 255;

    local max, min = math.max(r, g, b), math.min(r, g, b);
    local h, s, l = 0, 0, (max + min) / 2;

    if (max ~= min) then
        local d = max - min;
        s = (l > 0.5) and (d / (2 - max - min)) or (d / (max + min));

        if (max == r) then
            h = (g - b) / d + (g < b and 6 or 0);
        elseif (max == g) then
            h = (b - r) / d + 2;
        elseif (max == b) then
            h = (r - g) / d + 4;
        end -- if/elseif

        h = h / 6;
    end -- if

    return h, s, l;
end -- function

--[[
    Converts HSL back to RGB
    Returns: r, g, b
]]
function hsl_to_rgb(h, s, l)
    local r, g, b;

    if s == 0 then
        r = l * 255;
        g = l * 255;
        b = l * 255;
    else
        local function hue_to_rgb(t, p, q)
            if t < 0 then
                t = t + 1;
            end -- if

            if t > 1 then
                t = t - 1;
            end -- if

            return (t < 1/6) and (p + (q - p) * 6 * t) or
                   (t < 1/2) and q or
                   (t < 2/3) and (p + (q - p) * (2/3 - t) * 6) or
                   p;
        end -- function

        local q = (l < 0.5) and (l * (1 + s)) or (l + s - l * s);
        local p = 2 * l - q;

        r = hue_to_rgb(h + 1/3, p, q);
        g = hue_to_rgb(h, p, q);
        b = hue_to_rgb(h - 1/3, p, q);
    end -- if/else

    return math.floor(r * 255), math.floor(g * 255), math.floor(b * 255);
end -- function

--[[
    Description:
        Prints a string with altered color, given by the 'color' argument.
        Warning: The color must be present in the COLORS array.

    Example:
        color_say("red", "The sun is burning my skin!")

    Dependencies:
        https://metin2.dev/topic/29230-syreldars-useful-globals
]]
color_say = function(color, text)
    local color_coords = COLORS[color];
    if (color_coords == nil) then
        test_chat(string.format("ERROR: color %s is non-existent", color));
        return (text or "");
    end -- if

    local r, g, b = color_coords[1], color_coords[2], color_coords[3];
    say(color256(r, g, b)..text..color256(200, 200, 200))
end -- function

--[[
    Description:
        Returns a string with altered color, given by the 'color' argument. No select.
        Warning: The color must be present in the COLORS array.

    Example:
        say("I have red "..color_str("red", "eyes").." and brown "..color_str("brown", "hair").."!")

    Dependencies:
        https://metin2.dev/topic/29230-syreldars-useful-globals
]]
color_str = function(color, text)
    local color_coords = COLORS[color];
    if (color_coords == nil) then
        test_chat(string.format("ERROR: color %s is non-existent", color));
        return (text or "");
    end -- if

    local r, g, b = color_coords[1], color_coords[2], color_coords[3];
    return string.format("|cff%02x%02x%02x%s|r", r, g, b, text);
end -- function

--[[
    Description:
        Prints a string in a color that changes based on the proximity of a value to a given minimum and maximum.

    Arguments:
        min (number): The minimum value for the color gradient.
        max (number): The maximum value for the color gradient.
        value (number): The current value to evaluate within the defined range.
        text (string): The text to be printed in the dynamically determined color.

    Example:
        color_str_dynamic(0, 100, 50, "This is a test message!") -- Prints text in a color between red and green

    Returns:
        void: This function does not return a value; it prints the text directly.

    Time complexity: O(1)
    Space complexity: O(1)
]]
color_str_dynamic = function(min, max, value, text)
    if (value < min) then
        value = min;
    elseif (value > max) then
        value = max;
    end -- if/elseif

    local range = max - min;
    local ratio = (value - min) / range;

    local h = ratio * 120 / 360;
    local s = 1;
    local l = 0.5;

    local r, g, b = hsl_to_rgb(h, s, l);
    return string.format("|cff%02x%02x%02x%s|r", r, g, b, text);
end -- function

check_warp = function(wait_sec, warp_x, warp_y, warp_index)
    local time_passed_since_last_warp = get_time() - pc.getf("warp_time_check", "registered_time");
    local function can_warp()
        return time_passed_since_last_warp >= wait_sec and pc.can_warp();
    end -- local function

    if (not can_warp()) then
        say_reward("You have warped recently or you've recently opened")
        say_reward("a trade window in the last 10 seconds.")
        say_reward("Therefore, you gotta wait to be able to warp again.[ENTER]")
        if (select("Retry (ENTER)", "Close (ESC)") == SELECT.NO) then
            return;
        end -- if

        if (not can_warp()) then
            check_warp(wait_sec, warp_x, warp_y, warp_index);
            return;
        end -- if
    end -- if

    pc.setf("warp_time_check", "registered_time", get_time());
    setskin(NOWINDOW);
    if (warp_index == nil) then
        pc.warp(warp_x*100, warp_y*100);
    else
        pc.warp(warp_x*100, warp_y*100, warp_index);
    end -- if/else
end -- function
