import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Newspaper, User, Settings, LogOut, Trash2, Sun, Moon, ZoomIn, ZoomOut, Contrast, ChevronDown } from 'lucide-react';

export const HeaderBar = ({ backLink, backLabel }: { backLink?: string; backLabel?: string }) => {
  const [menuOpen, setMenuOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [fontSize, setFontSize] = useState(100);
  const [highContrast, setHighContrast] = useState(false);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle('dark');
  };

  const changeFontSize = (delta: number) => {
    const next = Math.min(150, Math.max(75, fontSize + delta));
    setFontSize(next);
    document.documentElement.style.fontSize = `${next}%`;
  };

  const toggleContrast = () => {
    setHighContrast(!highContrast);
    document.documentElement.classList.toggle('high-contrast');
  };

  return (
    <header className="border-b-2 border-foreground">
      <div className="container max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        {backLink ? (
          <Link to={backLink} className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors font-mono">
            ← {backLabel || 'Back'}
          </Link>
        ) : (
          <div className="flex items-center gap-2">
            <Newspaper className="w-5 h-5 text-primary" />
            <span className="font-mono text-xs text-muted-foreground tracking-wider uppercase">Est. 2026</span>
          </div>
        )}

        <Link to="/" className="flex items-center gap-2">
          <Newspaper className="w-4 h-4 text-primary" />
          <span className="font-display text-lg font-bold text-foreground">The Newsline</span>
        </Link>

        {/* Profile avatar + dropdown */}
        <div className="relative">
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="flex items-center gap-2 hover:opacity-80 transition-opacity"
          >
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
              <User className="w-4 h-4 text-primary-foreground" />
            </div>
            <ChevronDown className="w-3 h-3 text-muted-foreground" />
          </button>

          {menuOpen && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setMenuOpen(false)} />
              <div className="absolute right-0 top-full mt-2 w-64 bg-card border border-border shadow-lg z-50">
                {/* User info */}
                <div className="px-4 py-3 border-b border-border">
                  <Link to="/user/u1" className="font-mono text-sm font-semibold text-foreground hover:text-primary" onClick={() => setMenuOpen(false)}>
                    DataDrivenReader
                  </Link>
                  <p className="font-mono text-xs text-muted-foreground">Reputation: 87/100</p>
                </div>

                {/* Settings */}
                <div className="px-4 py-3 border-b border-border space-y-3">
                  <span className="font-mono text-xs text-muted-foreground uppercase tracking-wider">Display</span>

                  {/* Dark mode */}
                  <button onClick={toggleDarkMode} className="flex items-center justify-between w-full text-sm text-foreground hover:text-primary">
                    <span className="flex items-center gap-2">
                      {darkMode ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
                      <span className="font-mono text-xs">{darkMode ? 'Dark Mode' : 'Light Mode'}</span>
                    </span>
                    <span className="font-mono text-xs text-muted-foreground">{darkMode ? 'ON' : 'OFF'}</span>
                  </button>

                  {/* Font size */}
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs text-foreground flex items-center gap-2">
                      <Settings className="w-4 h-4" /> Font Size
                    </span>
                    <div className="flex items-center gap-1">
                      <button onClick={() => changeFontSize(-10)} className="p-1 hover:bg-accent rounded-sm">
                        <ZoomOut className="w-3.5 h-3.5 text-foreground" />
                      </button>
                      <span className="font-mono text-xs text-muted-foreground w-8 text-center">{fontSize}%</span>
                      <button onClick={() => changeFontSize(10)} className="p-1 hover:bg-accent rounded-sm">
                        <ZoomIn className="w-3.5 h-3.5 text-foreground" />
                      </button>
                    </div>
                  </div>

                  {/* High contrast */}
                  <button onClick={toggleContrast} className="flex items-center justify-between w-full text-sm text-foreground hover:text-primary">
                    <span className="flex items-center gap-2">
                      <Contrast className="w-4 h-4" />
                      <span className="font-mono text-xs">High Contrast</span>
                    </span>
                    <span className="font-mono text-xs text-muted-foreground">{highContrast ? 'ON' : 'OFF'}</span>
                  </button>
                </div>

                {/* Actions */}
                <div className="px-4 py-2">
                  <button className="flex items-center gap-2 w-full py-2 text-sm text-foreground hover:text-primary font-mono text-xs">
                    <LogOut className="w-4 h-4" /> Log Out
                  </button>
                  <button className="flex items-center gap-2 w-full py-2 text-sm text-destructive hover:text-destructive/80 font-mono text-xs">
                    <Trash2 className="w-4 h-4" /> Delete Account
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
};
