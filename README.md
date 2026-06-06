
### RPI sync

    rsync -av --exclude='.git' --exclude='**/__pycache__' --exclude='*.pyc' --exclude "binary" ~/work/Video\ to\ iDevice/video2iDevice/ rpi42:src/video2iDevice_v2/

or

    make deploy