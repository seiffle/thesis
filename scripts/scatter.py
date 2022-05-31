import sys

file_path = sys.argv[1]
chunk_num = int(sys.argv[2])
prefix = sys.argv[3]

with open(file_path) as input_file:
    line_count = sum(1 for line in input_file)


chunk_size = int(line_count / chunk_num)
chunk = ""
current_chunk = 1

with open(file_path) as input_file:
    for _ in range(chunk_num):
        if current_chunk == chunk_size:
            n = line_count - ((chunk_num - 1) * chunk_size)
        else:
            n = chunk_size

        for _ in range(n):
            line = input_file.readline()
            chunk += line
        with open(prefix + "{}-of-{}".format(current_chunk, chunk_num), "w") as output_file:
            output_file.write(chunk)
        chunk = ""
        current_chunk += 1
