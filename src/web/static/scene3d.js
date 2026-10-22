import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const VEHICLE_HEIGHT = .72;
const COLORS = [0xf2f4f8, 0xdde1e6, 0xc1c7cd, 0xa2a9b0, 0xe0e0e0, 0xc6c6c6];
const FOV = 38;

export function createCargoScene(host, { onSelect, onError } = {}) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'low-power' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  const canvas = renderer.domElement;
  canvas.setAttribute('role', 'img');
  canvas.setAttribute('aria-label', 'Tampilan 3D kapal. Pilih kendaraan melalui pemilih kendaraan; gunakan tombol kamera untuk navigasi.');
  canvas.style.cssText = 'display:block;width:100%;height:100%;touch-action:none;';
  host.append(canvas);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xf4f4f4);
  scene.fog = new THREE.Fog(0xf4f4f4, 40, 160);
  const camera = new THREE.PerspectiveCamera(FOV, 1, .05, 1000);
  camera.position.set(15, 20, 22);
  const controls = new OrbitControls(camera, canvas);
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  controls.enableDamping = !motion.matches;
  controls.dampingFactor = .15;
  controls.enablePan = true;
  controls.screenSpacePanning = true;
  controls.minPolarAngle = 0;
  controls.maxPolarAngle = Math.PI * .48;
  controls.enabled = false;

  scene.add(new THREE.HemisphereLight(0xffffff, 0x8d8d8d, 1.4));
  const sunlight = new THREE.DirectionalLight(0xffffff, 2.2);
  sunlight.castShadow = true;
  sunlight.shadow.mapSize.set(2048, 2048);
  sunlight.shadow.radius = 3;
  sunlight.shadow.bias = -.00025;
  sunlight.shadow.normalBias = .035;
  scene.add(sunlight, sunlight.target);
  const fill = new THREE.DirectionalLight(0xffffff, .5);
  fill.position.set(-20, 12, -10);
  scene.add(fill);

  const shared = new Set();
  const assets = new Set();
  const box = keep(new THREE.BoxGeometry(1, 1, 1), shared);
  const tire = keep(new THREE.CylinderGeometry(1, 1, 1, 10), shared);
  const square = keep(new THREE.BufferGeometry().setFromPoints([
    new THREE.Vector3(-.5, 0, -.5), new THREE.Vector3(.5, 0, -.5),
    new THREE.Vector3(.5, 0, .5), new THREE.Vector3(-.5, 0, .5),
  ]), shared);
  const boxEdges = keep(new THREE.EdgesGeometry(box), shared);
  const materials = {
    hull: standard(0x262626, .55, .25), boot: standard(0x525252, .6), rim: standard(0x6f6f6f), deck: standard(0x393939, .9),
    cabin: standard(0xffffff, .55, .1), glass: standard(0x393939, .25, .6), funnel: standard(0x0f62fe, .55),
    tire: standard(0x161616, .9),
    water: standard(0xc1c7cd, .62, .04),
    warning: glow(0xda1e28, .35), selected: glow(0x0f62fe, .3),
    headlight: standard(0xf4f4f4), taillight: standard(0x953f36),
    cars: COLORS.map(color => standard(color, .5, .3)),
    border: keep(new THREE.LineBasicMaterial({ color: 0x8d8d8d }), shared),
    footprint: keep(new THREE.LineBasicMaterial({ color: 0x6f6f6f, transparent: true, opacity: .75 }), shared),
    selectedLine: keep(new THREE.LineBasicMaterial({ color: 0x0f62fe, depthTest: false }), shared),
    warningLine: keep(new THREE.LineBasicMaterial({ color: 0xda1e28, depthTest: false }), shared),
    warningFill: keep(new THREE.MeshBasicMaterial({ color: 0xda1e28, transparent: true, opacity: .3, depthWrite: false, side: THREE.DoubleSide }), shared),
  };
  materials.rim.side = THREE.DoubleSide;
  const shipRoot = new THREE.Group();
  const cargoRoot = new THREE.Group();
  scene.add(shipRoot, cargoRoot);
  const selection = new THREE.LineLoop(square, materials.selectedLine);
  selection.visible = false;
  selection.renderOrder = 8;
  scene.add(selection);
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  const offset = new THREE.Vector3();
  const fleet = new Map();
  const visibleVehicles = [];
  const placements = [];
  let grid = null;
  let violationMesh = null;
  let structureKey = '';
  let deck = null;
  let state = null;
  let frame = 0;
  let active = false;
  let disposed = false;
  let contextLost = false;
  let drag = null;
  let pointerCount = 0;
  let hasCamera = false;
  let fitBounds = new THREE.Box3();

  function keep(resource, collection = assets) {
    collection.add(resource);
    return resource;
  }

  function standard(color, roughness = .72, metalness = .08) {
    return keep(new THREE.MeshStandardMaterial({ color, roughness, metalness }), shared);
  }

  function glow(color, intensity) {
    return keep(new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: intensity, roughness: .5, metalness: .1 }), shared);
  }

  materials.water.onBeforeCompile = (shader) => {
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec2 vWave;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvWave = (modelMatrix * vec4(position, 1.)).xz;');
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\nvarying vec2 vWave;')
      .replace('#include <map_fragment>', '#include <map_fragment>\ndiffuseColor.rgb *= .93 + .05 * sin(vWave.x * 1.7 + vWave.y * .45) + .03 * sin(vWave.y * 2.3 - vWave.x * .8);');
  };


  function mesh(parent, material, x, y, z, width, height, length, geometry = box) {
    const object = new THREE.Mesh(geometry, material);
    object.position.set(x, y, z);
    object.scale.set(width, height, length);
    object.castShadow = material !== materials.water;
    object.receiveShadow = true;
    parent.add(object);
    return object;
  }

  function line(parent, points, material, loop = false) {
    const geometry = keep(new THREE.BufferGeometry().setFromPoints(points.map(p => new THREE.Vector3(...p))));
    const object = loop ? new THREE.LineLoop(geometry, material) : new THREE.LineSegments(geometry, material);
    parent.add(object);
    return object;
  }

  function canRender() {
    return active && !disposed && !contextLost && !document.hidden && host.getClientRects().length > 0 && host.clientWidth > 0 && host.clientHeight > 0;
  }

  function requestRender() {
    if (!frame && canRender()) frame = requestAnimationFrame(render);
  }

  function render() {
    frame = 0;
    if (!canRender()) return;
    controls.update();
    renderer.render(scene, camera);
  }

  function stopRender() {
    if (frame) cancelAnimationFrame(frame);
    frame = 0;
  }

  function syncVisibility() {
    controls.enabled = canRender();
    if (controls.enabled) {
      resize();
      requestRender();
    } else {
      drag = null;
      pointerCount = 0;
      stopRender();
    }
  }

  function clearStructure() {
    violationMesh?.dispose();
    shipRoot.clear();
    cargoRoot.clear();
    for (const resource of assets) resource.dispose();
    assets.clear();
    fleet.clear();
    visibleVehicles.length = 0;
    placements.length = 0;
    grid = violationMesh = null;
    selection.visible = false;
    renderer.renderLists.dispose();
  }

  function buildShip(ship) {
    const width = ship.width, length = ship.length;
    const span = Math.max(width, length);
    const edge = Math.max(.3, Math.min(width, length) * .11);
    const stern = Math.max(.8, Math.min(width, length) * .36);
    const bow = Math.max(.8, Math.min(width, length) * .43);
    const depth = Math.max(.45, Math.min(width, length) * .16);
    const outline = [
      [-edge, -stern], [width + edge, -stern], [width + edge, length + edge],
      [width * .76, length + bow], [width * .24, length + bow], [-edge, length + edge],
    ];
    const hullShape = new THREE.Shape(outline.map(([x, z]) => new THREE.Vector2(x, z)));
    for (const [material, top, height] of [[materials.hull, -.12, depth * .55], [materials.boot, -.12 - depth * .55, depth * .45]]) {
      const geometry = keep(new THREE.ExtrudeGeometry(hullShape, { depth: height, bevelEnabled: false, steps: 1 }));
      geometry.rotateX(Math.PI / 2);
      const part = new THREE.Mesh(geometry, material);
      part.position.y = top;
      part.castShadow = part.receiveShadow = true;
      shipRoot.add(part);
    }
    const walkwayGeometry = keep(new THREE.ShapeGeometry(hullShape));
    walkwayGeometry.rotateX(Math.PI / 2);
    const walkway = new THREE.Mesh(walkwayGeometry, materials.rim);
    walkway.position.y = -.075;
    walkway.receiveShadow = true;
    shipRoot.add(walkway);
    mesh(shipRoot, materials.deck, width / 2, -.035, length / 2, width, .07, length);

    const gridCanvas = document.createElement('canvas');
    gridCanvas.width = gridCanvas.height = 64;
    const ctx = gridCanvas.getContext('2d');
    ctx.strokeStyle = 'rgba(141,141,141,.55)';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(.75, 64); ctx.lineTo(.75, .75); ctx.lineTo(64, .75); ctx.stroke();
    const gridTexture = keep(new THREE.CanvasTexture(gridCanvas));
    gridTexture.wrapS = gridTexture.wrapT = THREE.RepeatWrapping;
    gridTexture.repeat.set(width, length);
    gridTexture.anisotropy = Math.min(4, renderer.capabilities.getMaxAnisotropy());
    const gridMaterial = keep(new THREE.MeshBasicMaterial({ map: gridTexture, transparent: true, depthWrite: false, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -1 }));
    grid = new THREE.Mesh(keep(new THREE.PlaneGeometry(width, length)), gridMaterial);
    grid.rotation.x = -Math.PI / 2;
    grid.position.set(width / 2, .006, length / 2);
    shipRoot.add(grid);
    line(shipRoot, [[0, .025, 0], [width, .025, 0], [width, .025, length], [0, .025, length]], materials.border, true);

    const railHeight = Math.min(.42, edge * .8);
    const railPoints = [];
    for (let i = 0; i < outline.length; i++) {
      const [x, z] = outline[i], [nextX, nextZ] = outline[(i + 1) % outline.length];
      railPoints.push([x, railHeight, z], [nextX, railHeight, nextZ], [x, -.05, z], [x, railHeight, z]);
    }
    line(shipRoot, railPoints, materials.border);
    const cabinWidth = Math.min(width * .58, stern * 1.8);
    const cabinHeight = Math.min(1.8, Math.max(.6, width * .17));
    const cabinZ = -stern * .52;
    mesh(shipRoot, materials.cabin, width * .5, cabinHeight / 2, cabinZ, cabinWidth, cabinHeight, stern * .65);
    mesh(shipRoot, materials.glass, width * .5, cabinHeight * .67, cabinZ + stern * .33, cabinWidth * .86, cabinHeight * .25, .025);
    mesh(shipRoot, materials.cabin, width * .5, cabinHeight + .045, cabinZ, cabinWidth * 1.13, .09, stern * .77);
    mesh(shipRoot, materials.funnel, width * .5, cabinHeight + .38, cabinZ - stern * .16, Math.min(.4, cabinWidth * .25), .65, Math.min(.4, stern * .22));
    const mastPoints = [[width * .72, 0, cabinZ], [width * .72, cabinHeight * 1.65, cabinZ], [width * .65, cabinHeight * 1.4, cabinZ], [width * .79, cabinHeight * 1.4, cabinZ]];
    line(shipRoot, mastPoints, materials.border);
    const sea = new THREE.Mesh(keep(new THREE.PlaneGeometry(span * 16, span * 16)), materials.water);
    sea.rotation.x = -Math.PI / 2;
    sea.position.set(width / 2, -.12 - depth * .62, length / 2);
    sea.receiveShadow = true;
    shipRoot.add(sea);
    sunlight.position.set(width / 2 - span * .5, span * 1.2 + 6, length / 2 + span * .4);
    sunlight.target.position.set(width / 2, 0, length / 2);
    const shadowSpan = span * .85 + stern + bow;
    Object.assign(sunlight.shadow.camera, { left: -shadowSpan, right: shadowSpan, top: shadowSpan, bottom: -shadowSpan, near: .1, far: span * 4 + 30 });
    sunlight.shadow.camera.updateProjectionMatrix();
    fitBounds.set(new THREE.Vector3(-edge, -depth, -stern), new THREE.Vector3(width + edge, Math.max(cabinHeight * 1.65, VEHICLE_HEIGHT), length + bow));
  }

  function makeLabel(text) {
    const labelCanvas = document.createElement('canvas');
    labelCanvas.width = 512;
    labelCanvas.height = 96;
    const context = labelCanvas.getContext('2d');
    context.fillStyle = '#ffffff';
    context.fillRect(4, 8, 504, 80);
    context.strokeStyle = '#e0e0e0';
    context.lineWidth = 3;
    context.strokeRect(4, 8, 504, 80);
    context.fillStyle = '#161616';
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    context.font = '400 42px "IBM Plex Sans", sans-serif';
    let display = String(text);
    while (context.measureText(display).width > 464 && display.length > 1) display = display.slice(0, -1);
    if (display !== String(text)) display = display.slice(0, -1) + '…';
    context.fillText(display, 256, 50);
    const texture = keep(new THREE.CanvasTexture(labelCanvas));
    texture.colorSpace = THREE.SRGBColorSpace;
    const material = keep(new THREE.SpriteMaterial({ map: texture, depthTest: false, depthWrite: false, transparent: true }));
    const label = new THREE.Sprite(material);
    label.renderOrder = 10;
    label.raycast = () => {};
    return label;
  }

  function makeVehicle(vehicle, index) {
    const root = new THREE.Group();
    root.visible = false;
    root.userData.vehicleIndex = index;
    cargoRoot.add(root);
    const width = vehicle.width, length = vehicle.length, h = VEHICLE_HEIGHT;
    const paint = materials.cars[index % COLORS.length];
    const body = mesh(root, paint, 0, h * .34, 0, width * .86, h * .4, length * .92);
    const cabin = mesh(root, paint, 0, h * .68, -length * .06, width * .72, h * .32, length * .48);
    mesh(root, materials.glass, 0, h * .70, -length * .06, width * .735, h * .19, length * .49);
    mesh(root, paint, 0, h * .86, -length * .06, width * .73, h * .06, length * .49);
    for (const side of [-1, 1]) {
      for (const end of [-1, 1]) {
        const wheel = mesh(root, materials.tire, side * width * .435, h * .18, end * length * .30, h * .16, h * .18, h * .18, tire);
        wheel.rotation.z = Math.PI / 2;
        wheel.scale.set(Math.min(h * .18, length * .14), Math.min(h * .16, width * .12), Math.min(h * .18, length * .14));
        mesh(root, end === 1 ? materials.headlight : materials.taillight, side * width * .27, h * .35, end * length * .465, width * .17, h * .12, length * .015);
      }
    }
    const footprint = new THREE.LineLoop(square, materials.footprint);
    footprint.scale.set(width, 1, length);
    footprint.position.y = .035;
    footprint.raycast = () => {};
    root.add(footprint);
    const wire = new THREE.LineSegments(boxEdges, materials.warningLine);
    wire.scale.set(width, h, length);
    wire.position.y = h * .5;
    wire.visible = false;
    wire.renderOrder = 7;
    wire.raycast = () => {};
    root.add(wire);
    const entry = { root, body, cabin, footprint, wire, label: null, index, paint };
    fleet.set(index, entry);
    return entry;
  }

  function update({ problem, view, shipIndex, selectedVehicle, showGrid = true, showLabels = true }) {
    if (disposed || contextLost) return;
    const ship = problem?.ships?.[shipIndex];
    const key = JSON.stringify([shipIndex, ship?.id, ship?.width, ship?.length, problem?.vehicles?.map(v => [v.id, v.width, v.length])]);
    const changed = key !== structureKey;
    state = { problem, view, shipIndex, selectedVehicle, showGrid, showLabels };
    if (changed) {
      structureKey = key;
      clearStructure();
      deck = ship || null;
      hasCamera = false;
      if (ship) buildShip(ship);
    }
    visibleVehicles.length = 0;
    placements.length = 0;
    for (const entry of fleet.values()) entry.root.visible = false;
    selection.visible = false;
    if (!ship) {
      requestRender();
      return;
    }
    grid.visible = showGrid;
    problem.vehicles.forEach((vehicle, index) => {
      const position = view?.positions?.[index];
      if (!position || position[0] !== shipIndex) return;
      const x = position[1], z = position[2], orientation = position[3];
      const rotated = orientation === 'V';
      const width = rotated ? vehicle.length : vehicle.width;
      const length = rotated ? vehicle.width : vehicle.length;
      const entry = fleet.get(index) || makeVehicle(vehicle, index);
      entry.root.visible = true;
      entry.root.position.set(x + width / 2, 0, z + length / 2);
      entry.root.rotation.y = rotated ? Math.PI / 2 : 0;
      const invalid = x < 0 || z < 0 || x + width > ship.width || z + length > ship.length;
      placements.push({ entry, x, z, width, length, invalid });
      visibleVehicles.push(entry.root);
      if (showLabels && !entry.label) {
        entry.label = makeLabel(vehicle.id);
        entry.root.add(entry.label);
      }
      if (entry.label) {
        entry.label.visible = showLabels;
        const labelWidth = Math.min(3.2, Math.max(.8, width * .9));
        entry.label.scale.set(labelWidth, labelWidth * 96 / 512, 1);
        entry.label.position.set(0, VEHICLE_HEIGHT + .24, 0);
      }
    });
    const intersections = [];
    for (let a = 0; a < placements.length; a++) {
      for (let b = a + 1; b < placements.length; b++) {
        const first = placements[a], second = placements[b];
        const x = Math.max(first.x, second.x), z = Math.max(first.z, second.z);
        const right = Math.min(first.x + first.width, second.x + second.width);
        const far = Math.min(first.z + first.length, second.z + second.length);
        if (right > x && far > z) {
          first.invalid = second.invalid = true;
          intersections.push({ x, z, width: right - x, length: far - z });
        }
      }
    }
    for (const item of placements) {
      const { entry, invalid } = item;
      entry.body.material = entry.cabin.material = invalid ? materials.warning : entry.index === selectedVehicle ? materials.selected : entry.paint;
      entry.footprint.material = invalid ? materials.warningLine : materials.footprint;
      entry.wire.visible = invalid;
      if (entry.index === selectedVehicle) {
        selection.visible = true;
        selection.position.set(item.x + item.width / 2, .045, item.z + item.length / 2);
        selection.scale.set(item.width, 1, item.length);
      }
    }
    if (intersections.length && (!violationMesh || violationMesh.instanceMatrix.count < intersections.length)) {
      if (violationMesh) {
        cargoRoot.remove(violationMesh);
        violationMesh.dispose();
      }
      violationMesh = new THREE.InstancedMesh(box, materials.warningFill, intersections.length);
      violationMesh.frustumCulled = false;
      violationMesh.renderOrder = 6;
      cargoRoot.add(violationMesh);
    }
    if (violationMesh) {
      violationMesh.visible = intersections.length > 0;
      violationMesh.count = intersections.length;
      const matrix = new THREE.Matrix4();
      const scale = new THREE.Vector3();
      const translation = new THREE.Vector3();
      const rotation = new THREE.Quaternion();
      intersections.forEach((item, index) => {
        translation.set(item.x + item.width / 2, VEHICLE_HEIGHT + .015, item.z + item.length / 2);
        scale.set(item.width, .015, item.length);
        violationMesh.setMatrixAt(index, matrix.compose(translation, rotation, scale));
      });
      violationMesh.instanceMatrix.needsUpdate = true;
    }
    canvas.title = String(ship.id);
    canvas.setAttribute('aria-label', `Kapal ${ship.id}, area kemas ${ship.width} × ${ship.length} sel, ${placements.length} kendaraan. Tinggi hanya ilustrasi. Pemilihan dan detail lengkap tersedia pada pemilih kendaraan.`);
    if (changed || !hasCamera) resetView('iso');
    requestRender();
  }

  function currentBounds() {
    const bounds = fitBounds.clone();
    for (const item of placements) {
      bounds.expandByPoint(new THREE.Vector3(item.x, 0, item.z));
      bounds.expandByPoint(new THREE.Vector3(item.x + item.width, VEHICLE_HEIGHT + .4, item.z + item.length));
    }
    return bounds;
  }

  function resetView(preset = 'iso') {
    if (disposed || !deck) return;
    const bounds = currentBounds();
    const sphere = bounds.getBoundingSphere(new THREE.Sphere());
    const radius = Math.max(1, sphere.radius);
    controls.enableDamping = false;
    controls.update();
    controls.target.copy(sphere.center);
    if (preset === 'top') offset.set(0, radius * 2.5, .000001);
    else offset.set(radius * 2.2, radius * 1.5, radius * .35);
    controls.minTargetRadius = 0;
    controls.maxTargetRadius = radius * 8;
    controls.cursor.copy(sphere.center);
    const aspect = Math.max(1, host.clientWidth) / Math.max(1, host.clientHeight);
    const halfFov = THREE.MathUtils.degToRad(FOV / 2);
    const distance = radius / Math.sin(Math.min(halfFov, Math.atan(Math.tan(halfFov) * aspect))) * .66;
    camera.position.copy(controls.target).add(offset.setLength(distance));
    camera.near = distance / 200;
    camera.far = distance * 30;
    controls.minDistance = radius * .3;
    controls.maxDistance = distance * 4;
    scene.fog.near = distance * .9;
    scene.fog.far = distance * 3.2;
    controls.update();
    controls.enableDamping = !motion.matches;
    hasCamera = true;
    resize();
    requestRender();
  }

  function zoom(factor) {
    if (disposed || !Number.isFinite(factor) || factor <= 0) return;
    offset.copy(camera.position).sub(controls.target);
    offset.setLength(THREE.MathUtils.clamp(offset.length() / factor, controls.minDistance, controls.maxDistance));
    camera.position.copy(controls.target).add(offset);
    controls.update();
    requestRender();
  }

  function orbit(direction) {
    if (disposed || !deck || !direction) return;
    controls.enableDamping = false;
    controls.update();
    offset.copy(camera.position).sub(controls.target);
    if (Math.hypot(offset.x, offset.z) < offset.length() * .02) {
      const radius = offset.length();
      offset.set(radius * .65, radius * .72, radius * .65).setLength(radius);
    }
    offset.applyAxisAngle(THREE.Object3D.DEFAULT_UP, Math.sign(direction) * Math.PI / 8);
    camera.position.copy(controls.target).add(offset);
    controls.update();
    controls.enableDamping = !motion.matches;
    requestRender();
  }

  function focusVehicle(index) {
    if (disposed) return;
    const entry = fleet.get(index);
    if (!entry?.root.visible) return;
    controls.enableDamping = false;
    controls.update();
    offset.copy(camera.position).sub(controls.target);
    controls.target.copy(entry.root.position);
    camera.position.copy(controls.target).add(offset);
    controls.update();
    controls.enableDamping = !motion.matches;
    requestRender();
  }

  function resize() {
    if (disposed || contextLost) return;
    const width = host.clientWidth, height = host.clientHeight;
    if (!width || !height) return;
    const ratio = Math.min(window.devicePixelRatio || 1, 1.5);
    if (renderer.getPixelRatio() !== ratio) renderer.setPixelRatio(ratio);
    const size = renderer.getSize(new THREE.Vector2());
    if (size.x !== width || size.y !== height) renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    requestRender();
  }

  function setActive(value) {
    if (disposed) return;
    active = Boolean(value);
    syncVisibility();
  }

  function motionChange() {
    controls.enableDamping = !motion.matches;
    controls.update();
    requestRender();
  }

  function pick(event) {
    const rect = canvas.getBoundingClientRect();
    if (!rect.width || !rect.height) return null;
    pointer.set((event.clientX - rect.left) / rect.width * 2 - 1, -(event.clientY - rect.top) / rect.height * 2 + 1);
    raycaster.setFromCamera(pointer, camera);
    const hit = raycaster.intersectObjects(visibleVehicles, true)[0];
    if (!hit) return null;
    let object = hit.object;
    while (object && object.userData.vehicleIndex === undefined) object = object.parent;
    return object?.userData.vehicleIndex ?? null;
  }

  function pointerDown(event) {
    if (!canRender()) return;
    pointerCount++;
    if (pointerCount > 1 || event.button !== 0) { drag = null; return; }
    drag = { id: event.pointerId, x: event.clientX, y: event.clientY, moved: false };
  }

  function pointerMove(event) {
    if (!canRender()) return;
    if (drag && drag.id === event.pointerId) {
      if (Math.hypot(event.clientX - drag.x, event.clientY - drag.y) > 6) drag.moved = true;
      return;
    }
    if (pointerCount) return;
    const index = pick(event);
    canvas.style.cursor = index === null ? 'grab' : 'pointer';
    canvas.title = index === null ? String(deck?.id || '') : String(state.problem.vehicles[index].id);
  }

  function pointerUp(event) {
    pointerCount = Math.max(0, pointerCount - 1);
    const clicked = drag && drag.id === event.pointerId && !drag.moved && Math.hypot(event.clientX - drag.x, event.clientY - drag.y) <= 6;
    drag = null;
    if (!clicked || !canRender()) return;
    const index = pick(event);
    if (index !== null && typeof onSelect === 'function') onSelect(index);
  }

  function pointerCancel() {
    pointerCount = Math.max(0, pointerCount - 1);
    drag = null;
  }

  function contextLoss(event) {
    event.preventDefault();
    if (disposed || contextLost) return;
    contextLost = true;
    controls.enabled = false;
    stopRender();
    onError?.('Konteks WebGL terputus. Tampilan 3D dihentikan; gunakan tampilan 2D.');
  }

  const observer = new ResizeObserver(() => { syncVisibility(); });
  observer.observe(host);
  controls.addEventListener('change', requestRender);
  document.addEventListener('visibilitychange', syncVisibility);
  motion.addEventListener('change', motionChange);
  window.addEventListener('resize', resize);
  canvas.addEventListener('pointerdown', pointerDown);
  canvas.addEventListener('pointermove', pointerMove);
  canvas.addEventListener('pointerup', pointerUp);
  canvas.addEventListener('pointercancel', pointerCancel);
  canvas.addEventListener('webglcontextlost', contextLoss);

  function dispose() {
    if (disposed) return;
    disposed = true;
    stopRender();
    observer.disconnect();
    document.removeEventListener('visibilitychange', syncVisibility);
    motion.removeEventListener('change', motionChange);
    window.removeEventListener('resize', resize);
    canvas.removeEventListener('pointerdown', pointerDown);
    canvas.removeEventListener('pointermove', pointerMove);
    canvas.removeEventListener('pointerup', pointerUp);
    canvas.removeEventListener('pointercancel', pointerCancel);
    canvas.removeEventListener('webglcontextlost', contextLoss);
    controls.removeEventListener('change', requestRender);
    controls.dispose();
    clearStructure();
    for (const resource of shared) resource.dispose();
    shared.clear();
    sunlight.shadow.dispose();
    scene.clear();
    renderer.dispose();
    if (!contextLost) renderer.forceContextLoss();
    canvas.remove();
    state = deck = null;
  }

  return { update, setActive, resetView, zoom, orbit, focusVehicle, resize, dispose };
}
