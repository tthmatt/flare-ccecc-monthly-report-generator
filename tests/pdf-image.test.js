const assert = require("node:assert/strict");
const test = require("node:test");

const { normalizeForPdf } = require("../pdf-image.js");

test("normalizes browser images to JPEG bytes for reliable PDF embedding", async () => {
  const calls = [];
  const bitmap = { width: 1200, height: 800, close: () => calls.push("close") };
  const jpegBytes = Uint8Array.from([0xff, 0xd8, 0xff, 0xd9]);
  const context = {
    fillStyle: "",
    fillRect: (...args) => calls.push(["fillRect", ...args]),
    drawImage: (...args) => calls.push(["drawImage", ...args]),
  };
  const canvas = {
    width: 0,
    height: 0,
    getContext: type => type === "2d" ? context : null,
    toBlob: (callback, type, quality) => {
      calls.push(["toBlob", type, quality]);
      callback(new Blob([jpegBytes], { type }));
    },
  };

  const result = await normalizeForPdf({ name: "camera.webp" }, {
    createImageBitmap: async () => bitmap,
    createCanvas: () => canvas,
  });

  assert.equal(result.width, 1200);
  assert.equal(result.height, 800);
  assert.equal(result.format, "JPEG");
  assert.deepEqual([...result.data], [...jpegBytes]);
  assert.equal(context.fillStyle, "#ffffff");
  assert.deepEqual(calls[0], ["fillRect", 0, 0, 1200, 800]);
  assert.deepEqual(calls[1], ["drawImage", bitmap, 0, 0, 1200, 800]);
  assert.deepEqual(calls[2], ["toBlob", "image/jpeg", 0.92]);
  assert.equal(calls[3], "close");
  assert.equal(canvas.width, 0);
  assert.equal(canvas.height, 0);
});
