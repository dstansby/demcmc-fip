def parse_line(line: str) -> str:
    line = line.replace("_int", "")
    line_split = line.split("_")
    line_split[0] = line_split[0].capitalize()
    line_split[1] = line_split[1].upper()

    line_str = f"{line_split[0]} {line_split[1]} {line_split[2]}.{line_split[3]}"
    return line_str
