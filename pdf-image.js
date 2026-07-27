(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.PdfImage = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  async function normalizeForPdf(file, dependencies) {
    const deps = dependencies || {};
    const decode = deps.createImageBitmap || globalThis.createImageBitmap;
    const createCanvas =
      deps.createCanvas || (() => globalThis.document.createElement("canvas"));

    if (typeof decode !== "function") {
      throw new Error("This browser cannot decode images for PDF generation.");
    }

    const bitmap = await decode(file);
    const width = bitmap.width;
    const height = bitmap.height;
    const canvas = createCanvas();
    canvas.width = width;
    canvas.height = height;

    try {
      const context = canvas.getContext("2d");
      if (!context) throw new Error("Could not prepare an image canvas.");

      // PDF JPEGs cannot represent transparency. A white base also prevents
      // transparent PNG/WebP pixels from becoming black in PDF viewers.
      context.fillStyle = "#ffffff";
      context.fillRect(0, 0, width, height);
      context.drawImage(bitmap, 0, 0, width, height);

      const blob = await new Promise((resolve, reject) => {
        canvas.toBlob(
          value => value ? resolve(value) : reject(new Error("The browser could not encode this image.")),
          "image/jpeg",
          0.92
        );
      });

      return {
        width,
        height,
        data: new Uint8Array(await blob.arrayBuffer()),
        format: "JPEG",
      };
    } finally {
      bitmap.close();
      // Release the potentially large backing buffer as soon as it is encoded.
      canvas.width = 0;
      canvas.height = 0;
    }
  }

  return Object.freeze({ normalizeForPdf });
});
