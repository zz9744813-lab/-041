import { NavLink, Outlet } from 'react-router-dom';

const navItems = [
  { to: '/dashboard', icon: '📊', label: '数据看板' },
  { to: '/projects', icon: '📚', label: '我的项目' },
  { to: '/characters', icon: '👤', label: '角色设定', disabled: true },
  { to: '/world', icon: '🌍', label: '世界观', disabled: true },
  { to: '/settings', icon: '⚙️', label: '设置' },
];

export default function Layout() {
  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: 'var(--bg-primary)' }}>
      {/* Sidebar */}
      <aside
        style={{
          width: 240,
          flexShrink: 0,
          backgroundColor: 'var(--bg-secondary)',
          borderRight: '1px solid var(--border)',
          display: 'flex',
          flexDirection: 'column',
          padding: '24px 0',
          position: 'fixed',
          top: 0,
          left: 0,
          bottom: 0,
          zIndex: 50,
        }}
      >
        {/* Logo */}
        <div style={{ padding: '0 20px', marginBottom: 32 }}>
          <h1 style={{ fontSize: 20, fontWeight: 700, color: 'var(--accent)', margin: 0 }}>
            ✍️ 创作系统
          </h1>
        </div>

        {/* Navigation */}
        <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 4, padding: '0 8px' }}>
          {navItems.map((item) => {
            if (item.disabled) {
              return (
                <span
                  key={item.to}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    padding: '10px 12px',
                    borderRadius: 8,
                    fontSize: 14,
                    color: '#555',
                    cursor: 'not-allowed',
                    opacity: 0.5,
                  }}
                >
                  <span style={{ fontSize: 18 }}>{item.icon}</span>
                  {item.label}
                </span>
              );
            }
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/dashboard'}
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '10px 12px',
                  borderRadius: 8,
                  fontSize: 14,
                  textDecoration: 'none',
                  color: isActive ? 'var(--accent)' : 'var(--text-secondary)',
                  backgroundColor: isActive ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
                  fontWeight: isActive ? 600 : 400,
                  transition: 'all 0.15s ease',
                })}
              >
                <span style={{ fontSize: 18 }}>{item.icon}</span>
                {item.label}
              </NavLink>
            );
          })}
        </nav>

        {/* Version */}
        <div style={{ padding: '16px 20px', fontSize: 12, color: '#555', borderTop: '1px solid var(--border)' }}>
          v1.0.0
        </div>
      </aside>

      {/* Main content */}
      <main style={{ marginLeft: 240, flex: 1, minHeight: '100vh' }}>
        <Outlet />
      </main>
    </div>
  );
}