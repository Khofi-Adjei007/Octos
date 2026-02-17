const GRADIENTS = [
  'gradient-green',
  'gradient-blue',
  'gradient-purple',
  'gradient-orange',
  'gradient-red',
  'gradient-teal'
];

/**
 * Deterministic gradient selection.
 * Same branch → same gradient every time.
 */
function getGradientFromId(branchId) {
  return GRADIENTS[branchId % GRADIENTS.length];
}

export function applyBranchGradients() {

  const cards = document.querySelectorAll('.branch-card');

  if (!cards.length) return;

  cards.forEach((card) => {

    const branchId = parseInt(card.dataset.branchId, 10);

    if (isNaN(branchId)) return;

    const gradientClass = getGradientFromId(branchId);

    card.classList.remove(...GRADIENTS);
    card.classList.add(gradientClass);
  });
}
