export default function ImageGrid({ images, selected, onToggle, renderImage }) {
  return (
    <div className="image-grid">
      {images.map((img, i) => {
        const isSelected = selected?.includes(i);
        return (
          <button
            key={i}
            className={`image-grid__item ${isSelected ? "image-grid__item--selected" : ""}`}
            onClick={() => onToggle?.(i)}
          >
            {renderImage ? (
              renderImage(img, i)
            ) : (
              <img
                className="image-grid__img"
                src={img.thumbnail || img.src}
                alt={img.title || `Image ${i + 1}`}
                loading="lazy"
              />
            )}
            {isSelected && <div className="image-grid__check">✓</div>}
          </button>
        );
      })}
    </div>
  );
}
