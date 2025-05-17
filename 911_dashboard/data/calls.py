import kagglehub

# Download latest version
path = kagglehub.dataset_download("louisteitelbaum/911-recordings")

print("Path to dataset files:", path)