export type CompressionOptions = {
  maxDimension?: number;
  quality?: number;
};

export async function compressImage(
  file: File,
  options: CompressionOptions = {}
): Promise<File> {
  if (typeof window === "undefined" || !file.type.startsWith("image/")) {
    return file;
  }

  const maxDimension = options.maxDimension ?? 1600;
  const quality = options.quality ?? 0.8;

  try {
    const image = await loadImageFromFile(file);
    const { width, height } = fitDimensions(image.width, image.height, maxDimension);

    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext("2d");
    if (!ctx) return file;

    ctx.drawImage(image, 0, 0, width, height);

    const targetType = file.type === "image/png" ? "image/png" : "image/jpeg";
    const blob = await canvasToBlob(canvas, targetType, quality);
    if (!blob) return file;

    const ext = targetType === "image/png" ? "png" : "jpg";
    const baseName = file.name.replace(/\.[^.]+$/, "");
    const compressed = new File([blob], `${baseName}.${ext}`, { type: targetType });

    return compressed.size > 0 && compressed.size <= file.size ? compressed : file;
  } catch {
    return file;
  }
}

function fitDimensions(width: number, height: number, maxDimension: number) {
  if (width <= maxDimension && height <= maxDimension) {
    return { width, height };
  }

  const ratio = width / height;
  if (ratio >= 1) {
    return {
      width: maxDimension,
      height: Math.round(maxDimension / ratio),
    };
  }

  return {
    width: Math.round(maxDimension * ratio),
    height: maxDimension,
  };
}

function loadImageFromFile(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const image = new Image();
      image.onload = () => resolve(image);
      image.onerror = () => reject(new Error("image_load_failed"));
      image.src = String(reader.result);
    };
    reader.onerror = () => reject(new Error("file_read_failed"));
    reader.readAsDataURL(file);
  });
}

function canvasToBlob(
  canvas: HTMLCanvasElement,
  type: string,
  quality: number
): Promise<Blob | null> {
  return new Promise((resolve) => {
    canvas.toBlob((blob) => resolve(blob), type, quality);
  });
}
