def convert_temperature(value, from_scale, to_scale):
    from_scale = from_scale.lower()
    to_scale = to_scale.lower()

    if from_scale == "celsius":
        if to_scale == "fahrenheit":
            return (value * 9/5) + 32
        elif to_scale == "kelvin":
            return value + 273.15

    elif from_scale == "fahrenheit":
        if to_scale == "celsius":
            return (value - 32) * 5/9
        elif to_scale == "kelvin":
            return (value - 32) * 5/9 + 273.15

    elif from_scale == "kelvin":
        if to_scale == "celsius":
            return value - 273.15
        elif to_scale == "fahrenheit":
            return (value - 273.15) * 9/5 + 32

    elif from_scale == to_scale:
        return value

    else:
        raise ValueError("Invalid scale entered! Use Celsius, Fahrenheit, or Kelvin.")

# Example usage
temp = float(input("Enter temperature value: "))
from_scale = input("Enter from scale (Celsius/Fahrenheit/Kelvin): ")
to_scale = input("Enter to scale (Celsius/Fahrenheit/Kelvin): ")

try:
    result = convert_temperature(temp, from_scale, to_scale)
    print(f"{temp} {from_scale.capitalize()} = {result:.2f} {to_scale.capitalize()}")
except ValueError as e:
    print(e)
