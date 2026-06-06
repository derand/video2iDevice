RPI_HOST  := rpi42
RPI_PATH  := src/video2iDevice_v2/

RSYNC_FLAGS := -av --delete \
	--exclude='.git/' \
	--exclude='__pycache__/' \
	--exclude='*.pyc' \
	--exclude='tmp/' \
	--exclude='binary/' \
	--exclude='README.md' \
	--exclude='todo.md'

.PHONY: deploy deploy-dry

deploy:
	rsync $(RSYNC_FLAGS) ./ $(RPI_HOST):$(RPI_PATH)

deploy-dry:
	rsync $(RSYNC_FLAGS) --dry-run ./ $(RPI_HOST):$(RPI_PATH)
