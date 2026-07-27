(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.CceccSiteClassifier = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const EARTH_RADIUS_METERS = 6371008.8;
  const DEFAULT_MAX_DISTANCE_METERS = 750;
  const DEFAULT_MIN_LEAD_METERS = 20;

  const SITE_LOCATIONS = Object.freeze([
    Object.freeze({
      id: "tpe-pasir-ris",
      name: "TPE Pasir Ris",
      latitude: 1.3666775,
      longitude: 103.9525422,
    }),
    Object.freeze({
      id: "tpe-tampines",
      name: "TPE Tampines",
      latitude: 1.3649266,
      longitude: 103.9525216,
    }),
    Object.freeze({
      id: "pie-tampines",
      name: "PIE Tampines",
      latitude: 1.3460193,
      longitude: 103.9508788,
    }),
    Object.freeze({
      id: "pie-simei",
      name: "PIE Simei",
      latitude: 1.3445005,
      longitude: 103.952046,
    }),
  ]);

  function isValidCoordinate(latitude, longitude) {
    return (
      Number.isFinite(latitude) &&
      Number.isFinite(longitude) &&
      latitude >= -90 &&
      latitude <= 90 &&
      longitude >= -180 &&
      longitude <= 180
    );
  }

  function toRadians(value) {
    return (value * Math.PI) / 180;
  }

  function haversineMeters(latitudeA, longitudeA, latitudeB, longitudeB) {
    const latitudeDelta = toRadians(latitudeB - latitudeA);
    const longitudeDelta = toRadians(longitudeB - longitudeA);
    const latitudeARadians = toRadians(latitudeA);
    const latitudeBRadians = toRadians(latitudeB);

    const a =
      Math.sin(latitudeDelta / 2) ** 2 +
      Math.cos(latitudeARadians) *
        Math.cos(latitudeBRadians) *
        Math.sin(longitudeDelta / 2) ** 2;
    return 2 * EARTH_RADIUS_METERS * Math.asin(Math.sqrt(a));
  }

  function classifyCoordinate(latitude, longitude, options) {
    const settings = options || {};
    const maxDistanceMeters =
      settings.maxDistanceMeters ?? DEFAULT_MAX_DISTANCE_METERS;
    const minLeadMeters = settings.minLeadMeters ?? DEFAULT_MIN_LEAD_METERS;

    if (!isValidCoordinate(latitude, longitude)) {
      return {
        site: null,
        reason: "invalid-gps",
        distanceMeters: null,
        leadMeters: null,
        rankings: [],
      };
    }

    const rankings = SITE_LOCATIONS.map((site) => ({
      site,
      distanceMeters: haversineMeters(
        latitude,
        longitude,
        site.latitude,
        site.longitude
      ),
    })).sort((a, b) => a.distanceMeters - b.distanceMeters);

    const nearest = rankings[0];
    const runnerUp = rankings[1];
    const leadMeters = runnerUp.distanceMeters - nearest.distanceMeters;

    if (nearest.distanceMeters > maxDistanceMeters) {
      return {
        site: null,
        reason: "outside-site-range",
        distanceMeters: nearest.distanceMeters,
        leadMeters,
        rankings,
      };
    }

    if (leadMeters < minLeadMeters) {
      return {
        site: null,
        reason: "ambiguous-site",
        distanceMeters: nearest.distanceMeters,
        leadMeters,
        rankings,
      };
    }

    return {
      site: nearest.site,
      reason: null,
      distanceMeters: nearest.distanceMeters,
      leadMeters,
      rankings,
    };
  }

  return Object.freeze({
    SITE_LOCATIONS,
    DEFAULT_MAX_DISTANCE_METERS,
    DEFAULT_MIN_LEAD_METERS,
    haversineMeters,
    classifyCoordinate,
  });
});
