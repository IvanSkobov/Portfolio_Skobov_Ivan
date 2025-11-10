// Modal для просмотра скриншотов
document.addEventListener('DOMContentLoaded', () => {
	const modal = document.getElementById('screenshot-modal');
	const modalImg = document.getElementById('modal-image');
	const modalCaption = document.querySelector('.modal-caption');
	const closeBtn = document.querySelector('.modal-close');
	
	if (!modal || !modalImg || !closeBtn) {
		return; // Элементы не найдены, выходим
	}
	
	// Закрытие модального окна
	function closeModal() {
		modal.classList.remove('show');
		document.body.style.overflow = ''; // Разблокируем прокрутку
	}
	
	// Открытие модального окна при клике на скриншот
	document.querySelectorAll('.screenshot-thumb').forEach(img => {
		img.addEventListener('click', function(e) {
			e.stopPropagation(); // Предотвращаем переход по ссылке карточки
			e.preventDefault(); // Предотвращаем стандартное поведение
			modal.classList.add('show');
			modalImg.src = this.dataset.fullImage || this.src;
			if (modalCaption) {
				modalCaption.textContent = this.alt || 'Screenshot';
			}
			document.body.style.overflow = 'hidden'; // Блокируем прокрутку страницы
		});
	});
	
	// Закрытие модального окна
	closeBtn.addEventListener('click', closeModal);
	
	// Закрытие при клике вне изображения (на фон модального окна)
	modal.addEventListener('click', function(e) {
		if (e.target === modal) {
			closeModal();
		}
	});
	
	// Закрытие по ESC
	document.addEventListener('keydown', function(e) {
		if (e.key === 'Escape' && modal.classList.contains('show')) {
			closeModal();
		}
	});
	
	// Переход на GitHub при клике на карточку (кроме скриншотов)
	document.querySelectorAll('.project-card').forEach(card => {
		const repoUrl = card.dataset.repoUrl;
		if (repoUrl) {
			card.addEventListener('click', function(e) {
				// Проверяем, что клик не по скриншоту и не по области скриншотов
				if (!e.target.classList.contains('screenshot-thumb') && 
				    !e.target.closest('.shots')) {
					window.open(repoUrl, '_blank', 'noopener,noreferrer');
				}
			});
		}
	});
});

