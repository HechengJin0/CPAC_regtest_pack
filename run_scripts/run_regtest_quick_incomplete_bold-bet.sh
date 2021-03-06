#!/bin/bash

# usage
#   > ./run_regtest.sh {docker tag} {version name}

# for a c4.8xlarge
#   36 cpus
#   60 GB mem

# cpus/mem lower, meant to run two of these at the same time, set it and forget it

# WARNING
# incomplete = NO coverage of distortion correction, spike regression, and many other options etc.!
# this is meant entirely to get very quick numbers of the big basics
# this is NOT a full regression test meant for release validation

sudo docker run \
    -v /home/ubuntu:/home/ubuntu \
    -v /media/ebs/CPAC_regtest_pack:/media/ebs/CPAC_regtest_pack \
    -v /media/ebs/$2/ants:/output \
    $1 /home/ubuntu /output participant \
    --data_config_file /media/ebs/CPAC_regtest_pack/data_config_regtest_quick_incomplete.yml \
    --n_cpus 4 \
    --mem_gb 12 \
    --pipeline_override "num_ants_threads: 3" \
    --pipeline_override "numParticipantsAtOnce: 4" \
    --pipeline_override "functionalMasking: ['FSL']" \
    --pipeline_override "bold_bet_reduce_bias: On" \
    --pipeline_override "bold_bet_vertical_gradient: 0.4" \
    --save_working_dir
