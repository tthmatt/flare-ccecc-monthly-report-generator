const test = require("node:test");
const assert = require("node:assert/strict");

const {
  SITE_LOCATIONS,
  PRIORITY_ASSIGNMENT_ZONES,
  classifyCoordinate,
  haversineMeters,
} = require("../site-classifier.js");

test("each supplied site pin classifies to itself", () => {
  for (const site of SITE_LOCATIONS) {
    const result = classifyCoordinate(site.latitude, site.longitude);
    assert.equal(result.site?.id, site.id);
    assert.ok(result.distanceMeters < 0.01);
  }
});

test("nearby coordinates classify to the nearest site", () => {
  const site = SITE_LOCATIONS.find(({ id }) => id === "pie-simei");
  const result = classifyCoordinate(
    site.latitude + 0.00005,
    site.longitude - 0.00005
  );

  assert.equal(result.site?.id, "pie-simei");
  assert.ok(result.distanceMeters < 10);
});

test("coordinates far from every supplied pin remain unclassified", () => {
  const result = classifyCoordinate(1.29, 103.85);

  assert.equal(result.site, null);
  assert.equal(result.reason, "outside-site-range");
});

test("coordinates on the midpoint between close pins remain unclassified", () => {
  const pasirRis = SITE_LOCATIONS.find(({ id }) => id === "tpe-pasir-ris");
  const tampines = SITE_LOCATIONS.find(({ id }) => id === "tpe-tampines");
  const result = classifyCoordinate(
    (pasirRis.latitude + tampines.latitude) / 2,
    (pasirRis.longitude + tampines.longitude) / 2
  );

  assert.equal(result.site, null);
  assert.equal(result.reason, "ambiguous-site");
});

test("coordinates within the 5 m priority zone classify as TPE Pasir Ris", () => {
  const zone = PRIORITY_ASSIGNMENT_ZONES[0];
  const latitudeOffsetFor4Point999Meters =
    (4.999 / 6371008.8) * (180 / Math.PI);

  for (const latitude of [
    zone.latitude,
    zone.latitude + latitudeOffsetFor4Point999Meters,
  ]) {
    const result = classifyCoordinate(latitude, zone.longitude);
    assert.equal(result.site?.id, "tpe-pasir-ris");
    assert.equal(result.assignmentRule, "priority-zone");
  }
});

test("the 5 m priority zone does not override coordinates outside its radius", () => {
  const zone = PRIORITY_ASSIGNMENT_ZONES[0];
  const latitudeOffsetFor5Point1Meters =
    (5.1 / 6371008.8) * (180 / Math.PI);
  const result = classifyCoordinate(
    zone.latitude + latitudeOffsetFor5Point1Meters,
    zone.longitude
  );

  assert.notEqual(result.assignmentRule, "priority-zone");
});

test("haversine distance is symmetric", () => {
  const a = SITE_LOCATIONS[0];
  const b = SITE_LOCATIONS[1];
  const forward = haversineMeters(
    a.latitude,
    a.longitude,
    b.latitude,
    b.longitude
  );
  const reverse = haversineMeters(
    b.latitude,
    b.longitude,
    a.latitude,
    a.longitude
  );

  assert.ok(Math.abs(forward - reverse) < 0.000001);
  assert.ok(forward > 190 && forward < 200);
});
