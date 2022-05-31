process split {
    container 'ubuntu:latest'
    input:
    file input from Channel.fromPath('/mount/input.txt')

    output:
    file 'chunk_??' into input_channel

    """
    split.sh $input
    """
}

input_channel.flatten()
    .map { file ->
        def key = file.name.toString().tokenize('_').get(1)
        return tuple(key, file)
     }
    .groupTuple()
    .set{ groups_ch }

process chunk {
    container 'ubuntu:latest'
    input:
    tuple val(key), file(part) from groups_ch

    output:
    tuple val(key), file('input_*') into file_stream

    """
    split $part -l 250000 input_
    """
}

word_ch = file_stream.transpose()

process word_count {
    container 'python:latest'
    input:
    tuple val(key), file('input.txt') from word_ch

    output:
    tuple val(key), stdout into counted_ch

    """
    word_count.py
    """
}

process sort {
    container 'python:latest'
    input:
    tuple val(key), file('input.txt') from counted_ch

    output:
    tuple val(key), stdout into sorted_ch

    """
    sort.py
    """
}

sorted_ch.groupTuple()
    .map { tuple ->
        return tuple[1].flatten()
     }
     .set{ result_ch }

process merge {
    container 'python:latest'
    input:
    file x from result_ch

    output:
    stdout into result_merge

    """
    merge.py "$x"
    """
}

process calc {
    container 'python:latest'
    input:
    file 'result' from result_merge.collect()

    output:
    stdout into result

    """
    calc_deviance.py $result
    """
}
result.view()
