import { useState, useRef, useEffect, useId, type KeyboardEvent } from "react";

export interface CustomSelectOption {
  value: string;
  label: string;
}

interface CustomSelectProps {
  id?: string;
  name?: string;
  value: string;
  options: CustomSelectOption[];
  placeholder?: string;
  disabled?: boolean;
  onChange: (value: string) => void;
  className?: string;
  "aria-label"?: string;
}

export function CustomSelect({
  id: propId,
  name,
  value,
  options,
  placeholder = "Choose a project",
  disabled = false,
  onChange,
  className = "",
  "aria-label": ariaLabel,
}: CustomSelectProps) {
  const generatedId = useId();
  const selectId = propId || generatedId;
  const [isOpen, setIsOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLUListElement>(null);

  // Close when clicking outside
  useEffect(() => {
    if (!isOpen) return;
    function handlePointerDown(e: PointerEvent | MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, [isOpen]);

  // Adjust focused item on open
  useEffect(() => {
    if (isOpen) {
      const idx = options.findIndex((o) => o.value === value);
      setFocusedIndex(idx >= 0 ? idx : 0);
    } else {
      setFocusedIndex(-1);
    }
  }, [isOpen, options, value]);

  // Scroll focused option into view
  useEffect(() => {
    if (isOpen && focusedIndex >= 0 && menuRef.current) {
      const item = menuRef.current.children[focusedIndex] as HTMLElement | undefined;
      item?.scrollIntoView({ block: "nearest" });
    }
  }, [focusedIndex, isOpen]);

  const selectedOption = options.find((o) => o.value === value);
  const displayLabel = selectedOption?.value ? selectedOption.label : placeholder;

  function handleSelect(val: string) {
    setIsOpen(false);
    triggerRef.current?.focus();
    onChange(val);
  }

  function handleKeyDown(e: KeyboardEvent<HTMLButtonElement>) {
    if (disabled) return;

    if (e.key === "ArrowDown" || e.key === "Down") {
      e.preventDefault();
      if (!isOpen) {
        setIsOpen(true);
      } else {
        setFocusedIndex((prev) => (prev < options.length - 1 ? prev + 1 : 0));
      }
    } else if (e.key === "ArrowUp" || e.key === "Up") {
      e.preventDefault();
      if (!isOpen) {
        setIsOpen(true);
      } else {
        setFocusedIndex((prev) => (prev > 0 ? prev - 1 : options.length - 1));
      }
    } else if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      if (isOpen && focusedIndex >= 0 && options[focusedIndex]) {
        handleSelect(options[focusedIndex].value);
      } else {
        setIsOpen((prev) => !prev);
      }
    } else if (e.key === "Escape" || e.key === "Esc") {
      if (isOpen) {
        e.preventDefault();
        setIsOpen(false);
        triggerRef.current?.focus();
      }
    } else if (e.key === "Tab") {
      if (isOpen) {
        setIsOpen(false);
      }
    }
  }

  return (
    <div
      ref={containerRef}
      className={`custom-select-wrapper ${isOpen ? "open" : ""} ${disabled ? "disabled" : ""} ${className}`}
    >
      {/* 
        Native select: kept visually hidden behind the custom UI so:
        - page.getByLabel('Existing project').selectOption(...) works seamlessly in E2E tests
        - expect(...).toHaveValue(...) works seamlessly
        - expect(...).locator('option:checked') works seamlessly
      */}
      <select
        id={selectId}
        name={name}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        tabIndex={-1}
        aria-hidden="true"
        className="custom-select-native"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>

      {/* Styled custom trigger button */}
      <button
        ref={triggerRef}
        type="button"
        className={`custom-select-trigger ${!selectedOption?.value ? "is-placeholder" : ""}`}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label={ariaLabel}
        disabled={disabled}
        onClick={() => !disabled && setIsOpen((prev) => !prev)}
        onKeyDown={handleKeyDown}
      >
        <span className="custom-select-text">{displayLabel}</span>
        <svg
          className={`custom-select-arrow ${isOpen ? "rotated" : ""}`}
          width="12"
          height="12"
          viewBox="0 0 12 12"
          aria-hidden="true"
        >
          <path
            d="M2.5 4.5L6 8L9.5 4.5"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>

      {/* Custom styled in-page dropdown menu */}
      {isOpen && (
        <ul
          ref={menuRef}
          className="custom-select-menu"
          role="listbox"
          tabIndex={-1}
        >
          {options.map((opt, idx) => {
            const isSelected = opt.value === value;
            const isFocused = idx === focusedIndex;
            return (
              <li
                key={opt.value}
                role="option"
                aria-selected={isSelected}
                className={`custom-select-option ${isSelected ? "selected" : ""} ${isFocused ? "focused" : ""} ${opt.value === "" ? "placeholder-option" : ""}`}
                onClick={() => handleSelect(opt.value)}
                onMouseEnter={() => setFocusedIndex(idx)}
              >
                <span className="option-label">{opt.label}</span>
                {isSelected && (
                  <svg
                    className="option-check"
                    width="14"
                    height="14"
                    viewBox="0 0 14 14"
                    aria-hidden="true"
                  >
                    <path
                      d="M3 7.2L5.4 9.6L11 4"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.75"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
