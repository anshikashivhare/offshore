import re

with open('frontend/src/pages/Home.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Add import for TriangleAlert
content = content.replace('Map as MapIcon,', 'Map as MapIcon,\n  TriangleAlert,')

# Add isImmersive definition
content = content.replace(
    'const showFooter = viewMode !== "navigation";',
    'const isImmersive = viewMode === "navigation" || viewMode === "risk";\n  const showFooter = !isImmersive;'
)

# Replace conditions
content = content.replace('viewMode === "navigation" ? "navigation-view-active"', 'isImmersive ? "navigation-view-active"')
content = content.replace('{viewMode !== "navigation" && (', '{!isImmersive && (')
content = content.replace('viewMode === "navigation" ? "navigation-fullscreen-active"', 'isImmersive ? "navigation-fullscreen-active"')
content = content.replace('isFullscreen || viewMode === "navigation"', 'isFullscreen || isImmersive')
content = content.replace('viewMode === "navigation" ? "map-header-nav-floating"', 'isImmersive ? "map-header-nav-floating"')

# Update eyebrow
content = content.replace(
    '<span className="eyebrow">{viewMode === "navigation" ? "OFFSHORE · VOYAGE NAVIGATION" : "MISSION 08 · ROUTE PLANNING"}</span>',
    '<span className="eyebrow">{viewMode === "navigation" ? "OFFSHORE · VOYAGE NAVIGATION" : viewMode === "risk" ? "OFFSHORE · RISK ANALYSIS" : "MISSION 08 · ROUTE PLANNING"}</span>'
)

# Add Risk tab
risk_tab = '''                <button
                  className={`toggle-tab-btn ${viewMode === "navigation" ? "active" : ""}`}
                  onClick={() => setViewMode("navigation")}
                  aria-label="Navigation voyage view"
                  title="Navigation / Voyage Mode (Pitched 3D Perspective Follow)"
                >
                  <Compass size={14} />
                  <span>Navigation</span>
                </button>
                <button
                  className={`toggle-tab-btn ${viewMode === "risk" ? "active" : ""}`}
                  onClick={() => setViewMode("risk")}
                  aria-label="Risk view"
                  title="Risk Analysis View"
                >
                  <TriangleAlert size={14} />
                  <span>Risk</span>
                </button>'''

content = content.replace(
    '                <button\n                  className={`toggle-tab-btn ${viewMode === "navigation" ? "active" : ""}`}\n                  onClick={() => setViewMode("navigation")}\n                  aria-label="Navigation voyage view"\n                  title="Navigation / Voyage Mode (Pitched 3D Perspective Follow)"\n                >\n                  <Compass size={14} />\n                  <span>Navigation</span>\n                </button>',
    risk_tab
)

with open('frontend/src/pages/Home.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
