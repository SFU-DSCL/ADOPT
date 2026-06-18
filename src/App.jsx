import { useEffect, useMemo, useState } from "react";
import {
  Activity, AlertTriangle, Anchor, Boxes, Building2, CalendarDays, ChevronLeft,
  ChevronRight, CircleHelp, Container, Filter, Gauge, Layers3, Map as MapIcon,
  PanelLeftClose, PanelLeftOpen, Play, Pause, TrainFront, Search, Settings,
  Ship, Truck, Warehouse, X, ZoomIn, ZoomOut
} from "lucide-react";

const NAV_ITEMS = [
  ["Network map", MapIcon], ["Control tower", Gauge], ["Terminal operations", Anchor],
  ["Shipments", Truck], ["Containers", Container], ["Warehouses", Warehouse],
  ["Rail transfers", TrainFront], ["Analytics", Activity], ["Exceptions", AlertTriangle],
];

const LOCATION_ICONS = { port: Anchor, warehouse: Warehouse, crossdock: Boxes, rail: TrainFront };
const MAP_BOUNDS = { west: -123.35, east: -122.45, north: 49.40, south: 48.98 };
const CITY_LABELS = [
  { name: "Vancouver", lat: 49.265, lon: -123.120 },
  { name: "Burnaby", lat: 49.248, lon: -122.980 },
  { name: "Surrey", lat: 49.185, lon: -122.850 },
  { name: "Langley", lat: 49.104, lon: -122.660 },
  { name: "Delta", lat: 49.084, lon: -123.060 },
  { name: "Richmond", lat: 49.166, lon: -123.135 },
];

function project({ lat, lon }) {
  const mercator = value => Math.log(Math.tan(Math.PI / 4 + value * Math.PI / 360));
  const north = mercator(MAP_BOUNDS.north);
  const south = mercator(MAP_BOUNDS.south);
  return {
    x: ((lon - MAP_BOUNDS.west) / (MAP_BOUNDS.east - MAP_BOUNDS.west)) * 100,
    y: ((north - mercator(lat)) / (north - south)) * 100,
  };
}

function Sidebar({ collapsed, onCollapse, onSoon }) {
  return <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
    <nav aria-label="Primary navigation">
      {NAV_ITEMS.map(([label, Icon], index) => <button
        key={label}
        className={`nav-item ${index === 0 ? "active" : ""}`}
        onClick={() => index ? onSoon(label) : null}
        title={collapsed ? label : undefined}
      ><Icon size={20}/><span>{label}</span>{label === "Exceptions" && <b>12</b>}</button>)}
    </nav>
    <div className="side-foot">
      {!collapsed && <div><span>Planning horizon</span><strong>365 days</strong><small>Jul 2026 — Jun 2027</small></div>}
      <button className="collapse-button" onClick={onCollapse} aria-label="Collapse sidebar">
        {collapsed ? <PanelLeftOpen size={18}/> : <><PanelLeftClose size={18}/><span>Collapse</span></>}
      </button>
    </div>
  </aside>;
}

function Marker({ location, active, onClick }) {
  const Icon = LOCATION_ICONS[location.type] || Building2;
  const point = project(location);
  return <button
    className={`map-marker ${location.type} ${active ? "selected" : ""}`}
    style={{ left: `${point.x}%`, top: `${point.y}%` }}
    onClick={() => onClick(location)}
  >
    <span className="marker-icon"><Icon size={16}/></span>
    <span className="marker-label"><strong>{location.name}</strong><small>{location.capacity} {location.capacity_unit}</small></span>
  </button>;
}

function CustomerMarker({ customer, onClick }) {
  const point = project(customer);
  return <button className="customer-marker" style={{ left: `${point.x}%`, top: `${point.y}%` }} onClick={() => onClick(customer)} title={customer.display_name}>
    <span></span>
  </button>;
}

function RouteLayer({ routes, locations, customers, selectedId, onSelect, tick }) {
  const locationMap = useMemo(() => new Map(locations.map(item => [item.location_id, item])), [locations]);
  const customerMap = useMemo(() => new Map(customers.map(item => [item.customer_id, item])), [customers]);
  return <svg className="routes" viewBox="0 0 100 100" preserveAspectRatio="none" aria-label="Active drayage routes">
    {routes.map((route, index) => {
      const start = locationMap.get(route.port); const mid = locationMap.get(route.warehouse); const end = customerMap.get(route.customer);
      if (!start || !mid || !end) return null;
      const a = project(start); const b = project(mid); const c = project(end);
      const d = `M ${a.x} ${a.y} Q ${(a.x + b.x) / 2} ${Math.min(a.y, b.y) - 5} ${b.x} ${b.y} Q ${(b.x + c.x) / 2} ${(b.y + c.y) / 2 - 3} ${c.x} ${c.y}`;
      return <g key={route.id} className={`route-group ${route.status} ${selectedId === route.id ? "selected" : ""}`} onClick={() => onSelect(route)}>
        <path className="route-hit" d={d}/><path className="route-path" d={d}/>
        <circle className="route-vehicle" r="0.85">
          <animateMotion dur={`${14 + index}s`} repeatCount="indefinite" path={d} begin={`${-tick - index}s`}/>
        </circle>
      </g>;
    })}
  </svg>;
}

function Inspector({ selection, route, locations, customers, onClose }) {
  const locationMap = new Map(locations.map(item => [item.location_id, item]));
  const customerMap = new Map(customers.map(item => [item.customer_id, item]));
  if (selection?.location_id) return <aside className="inspector">
    <button className="inspector-close" onClick={onClose}><X size={19}/></button>
    <div className={`inspector-symbol ${selection.type}`}><span>{selection.type === "port" ? <Anchor/> : selection.type === "rail" ? <TrainFront/> : <Warehouse/>}</span></div>
    <p className="inspector-overline">{selection.type === "crossdock" ? "Cross-dock facility" : selection.type}</p>
    <h2>{selection.name}</h2>
    <p className="inspector-muted">{selection.city} · ADOPT network asset</p>
    <div className="capacity-block"><span>Configured capacity</span><strong>{selection.capacity}</strong><small>{selection.capacity_unit}</small></div>
    <h3>Live operating state</h3>
    <dl className="detail-grid"><div><dt>Utilization</dt><dd>{selection.type === "port" ? "76%" : "64%"}</dd></div><div><dt>Current queue</dt><dd>{selection.type === "port" ? "18 containers" : "7 moves"}</dd></div><div><dt>Next window</dt><dd>14:30 PDT</dd></div><div><dt>Status</dt><dd className="healthy">Healthy</dd></div></dl>
    <button className="inspector-action" onClick={() => alert(`${selection.name} detail page is queued for the next prototype pass.`)}>View operations</button>
  </aside>;

  const start = locationMap.get(route.port); const mid = locationMap.get(route.warehouse); const end = customerMap.get(route.customer);
  return <aside className="inspector">
    <button className="inspector-close" onClick={onClose}><X size={19}/></button>
    <p className="inspector-overline">Selected container</p><h2>{route.id}</h2><p className="inspector-muted">{route.product}</p>
    <div className="route-summary"><span className={route.status}></span><strong>{route.status.replace("_", " ")}</strong><small>{Math.round(route.progress * 100)}% complete</small></div>
    <h3>Journey</h3>
    <ol className="journey">
      <li className="done"><i>1</i><div><strong>Discharged</strong><span>{start?.name}</span></div><time>08:20</time></li>
      <li className="done"><i>2</i><div><strong>Gate out</strong><span>Gate {Number(route.id.slice(-2)) % 10 + 1}</span></div><time>10:05</time></li>
      <li className="active"><i>3</i><div><strong>Warehouse transfer</strong><span>{mid?.name}</span></div><time>13:40</time></li>
      <li><i>4</i><div><strong>Customer delivery</strong><span>{end?.display_name}</span></div><time>17:15</time></li>
    </ol>
    <h3>Move detail</h3>
    <dl className="detail-grid"><div><dt>Container</dt><dd>40′ High Cube</dd></div><div><dt>Carrier</dt><dd>Harbour Link</dd></div><div><dt>Chassis</dt><dd>CHS-{route.id.slice(-4)}</dd></div><div><dt>Priority</dt><dd>Standard</dd></div></dl>
  </aside>;
}

export function App() {
  const [data, setData] = useState(null);
  const [collapsed, setCollapsed] = useState(false);
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [playing, setPlaying] = useState(true);
  const [timeIndex, setTimeIndex] = useState(164);
  const [status, setStatus] = useState("all");
  const [type, setType] = useState("all");
  const [search, setSearch] = useState("");
  const [zoom, setZoom] = useState(1);
  const [toast, setToast] = useState("");
  const [tick, setTick] = useState(0);

  useEffect(() => { fetch("/data/manifest.json").then(r => r.json()).then(value => { setData(value); setSelectedRoute(value.sample_routes[1]); }); }, []);
  useEffect(() => {
    if (!playing) return undefined;
    const timer = setInterval(() => { setTimeIndex(value => (value + 1) % 365); setTick(value => value + 1); }, 2200);
    return () => clearInterval(timer);
  }, [playing]);
  useEffect(() => { if (!toast) return undefined; const timer = setTimeout(() => setToast(""), 2600); return () => clearTimeout(timer); }, [toast]);

  if (!data) return <div className="loading"><Ship size={32}/><strong>Loading ADOPT network…</strong></div>;
  const routes = data.sample_routes.filter(route => (status === "all" || route.status === status) && (type === "all" || route.product.toLowerCase().includes(type)));
  const locations = data.locations.filter(item => item.name.toLowerCase().includes(search.toLowerCase()) || item.city.toLowerCase().includes(search.toLowerCase()));
  const currentDay = new Date(`${data.start_date}T12:00:00`); currentDay.setDate(currentDay.getDate() + timeIndex);
  const fmt = new Intl.DateTimeFormat("en-CA", { month: "short", day: "numeric", year: "numeric" });
  const metrics = [
    [Ship, "Vessel calls", "3,650", "10 arrivals today", "blue"],
    [Container, "Annual containers", "73,000", "200 scheduled today", "teal"],
    [Truck, "Moves in transit", "84", "+6 since 08:00", "orange"],
    [AlertTriangle, "Exceptions", "12", "3 need action", "red"],
  ];

  const selectLocation = item => { setSelectedLocation(item); setSelectedRoute(null); };
  const selectRoute = item => { setSelectedRoute(item); setSelectedLocation(null); };
  return <div className={`app ${collapsed ? "is-collapsed" : ""}`}>
    <header className="topbar">
      <div className="brand"><span className="brand-mark"><span></span></span><div><strong>ADOPT</strong><small>Advanced Drayage Optimizer</small></div></div>
      <div className="live-time"><i></i><span>Live network</span><strong>{fmt.format(currentDay)} · 10:28 PDT</strong></div>
      <div className="header-actions"><button onClick={() => setToast("Annual scenario is already loaded")}><CalendarDays/>Annual scenario</button><button aria-label="Help"><CircleHelp/></button><button aria-label="Settings"><Settings/></button><span className="avatar">SO</span></div>
    </header>
    <Sidebar collapsed={collapsed} onCollapse={() => setCollapsed(value => !value)} onSoon={label => setToast(`${label} is coming in the next ADOPT build`)} />
    <main className="main-content">
      <section className="page-head"><div><h1>Vancouver Lower Mainland</h1><p>Port, rail, warehouse and customer network</p></div><div className="map-tools"><button><Filter/>Filters</button><button><Layers3/>Layers</button><label><Search/><input value={search} onChange={event => setSearch(event.target.value)} placeholder="Search location"/></label></div></section>
      <section className="metric-strip">{metrics.map(([Icon, label, value, detail, color]) => <div className="metric" key={label}><span className={`metric-icon ${color}`}><Icon/></span><div><small>{label}</small><strong>{value}</strong><em>{detail}</em></div></div>)}</section>
      <section className="network-shell">
        <div className="map-panel">
          <div className="map-stage" style={{ "--zoom": zoom }}>
            <div className="map-art"></div>
            <RouteLayer routes={routes} locations={data.locations} customers={data.customers_detail} selectedId={selectedRoute?.id} onSelect={selectRoute} tick={tick}/>
            <div className="map-labels">{CITY_LABELS.map(city => { const point = project(city); return <span key={city.name} style={{left:`${point.x}%`,top:`${point.y}%`}}>{city.name}</span>; })}</div>
            {locations.map(item => <Marker key={item.location_id} location={item} active={selectedLocation?.location_id === item.location_id} onClick={selectLocation}/>)}
            {data.customers_detail.map(item => <CustomerMarker key={item.customer_id} customer={item} onClick={() => { setToast(item.display_name); }}/>) }
          </div>
          <div className="map-filters"><select value={status} onChange={event => setStatus(event.target.value)}><option value="all">All movement</option><option value="planned">Planned</option><option value="in_transit">In transit</option><option value="delivered">Delivered</option><option value="late">Late</option></select><select value={type} onChange={event => setType(event.target.value)}><option value="all">All products</option><option value="furniture">Furniture</option><option value="frozen">Cold chain</option><option value="floor">Building materials</option><option value="computer">Electronics</option></select></div>
          <div className="zoom-controls"><button onClick={() => setZoom(value => Math.min(1.35, value + .1))}><ZoomIn/></button><button onClick={() => setZoom(value => Math.max(.9, value - .1))}><ZoomOut/></button></div>
          <div className="legend"><strong>Network</strong><span><i className="port"></i>Port terminal</span><span><i className="warehouse"></i>Warehouse / DC</span><span><i className="rail"></i>BC Rail</span><span><i className="customer"></i>Customer site</span><span><b className="planned"></b>Planned</span><span><b className="moving"></b>In transit</span><span><b className="late"></b>Late</span></div>
          <a className="map-attribution" href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">© OpenStreetMap contributors</a>
        </div>
        <Inspector selection={selectedLocation} route={selectedRoute || data.sample_routes[0]} locations={data.locations} customers={data.customers_detail} onClose={() => { setSelectedRoute(data.sample_routes[0]); setSelectedLocation(null); }}/>
      </section>
      <section className="playback"><button className="play" onClick={() => setPlaying(value => !value)}>{playing ? <Pause fill="currentColor"/> : <Play fill="currentColor"/>}<span>{playing ? "Pause" : "Play"}</span></button><button className="speed">1× <ChevronRight size={14}/></button><div className="date-readout"><small>Simulation date</small><strong>{fmt.format(currentDay)}</strong><span>LIVE</span></div><div className="range-wrap"><input type="range" min="0" max="364" value={timeIndex} onChange={event => setTimeIndex(Number(event.target.value))}/><div><span>Jul</span><span>Sep</span><span>Dec</span><span>Mar</span><span>Jun</span></div></div><div className="day-nav"><button onClick={() => setTimeIndex(value => Math.max(0, value - 1))}><ChevronLeft/></button><button onClick={() => setTimeIndex(value => Math.min(364, value + 1))}><ChevronRight/></button></div></section>
    </main>
    {toast && <div className="toast">{toast}</div>}
  </div>;
}
