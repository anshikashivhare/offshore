import re

with open('frontend/src/components/OffshoreMap.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Import RiskModePanel
if 'from "./RiskModePanel"' not in content:
    content = content.replace(
        'import { IcebergsMapLayer } from "./IcebergsMapLayer";',
        'import { IcebergsMapLayer } from "./IcebergsMapLayer";\nimport { RiskModePanel } from "./RiskModePanel";'
    )

# Replace viewMode !== "navigation" with viewMode !== "navigation" && viewMode !== "risk"
content = content.replace(
    '{viewMode !== "navigation" && (',
    '{viewMode !== "navigation" && viewMode !== "risk" && ('
)
content = content.replace(
    '{viewMode !== "navigation" && <NauticalMapControls',
    '{viewMode !== "navigation" && viewMode !== "risk" && <NauticalMapControls'
)
content = content.replace(
    '{viewMode !== "navigation" && layers.seaIceConcentration !== false && <SeaIceLegend />}',
    '{viewMode !== "navigation" && viewMode !== "risk" && layers.seaIceConcentration !== false && <SeaIceLegend />}'
)
content = content.replace(
    '{viewMode !== "navigation" && <DataAttribution',
    '{viewMode !== "navigation" && viewMode !== "risk" && <DataAttribution'
)

# Add RiskModePanel logic
risk_hud = '''      {/* ============ RISK MODE HUD ============ */}
      {viewMode === "risk" && (
        <RiskModePanel onExit={() => onExitNavigation?.()} />
      )}
'''
if 'RiskModePanel onExit=' not in content:
    content = content.replace(
        '{/* ============ NAVIGATION HUD',
        risk_hud + '\n      {/* ============ NAVIGATION HUD'
    )

# Update ports layer
content = content.replace(
    'isNavMode={viewMode === "navigation"}',
    'isNavMode={viewMode === "navigation" || viewMode === "risk"}'
)

with open('frontend/src/components/OffshoreMap.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done!')
