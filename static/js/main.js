// Mobile menu toggle
        const mobileMenuBtn = document.getElementById('mobile-menu-btn');
        const mobileMenu = document.getElementById('mobile-menu');
        mobileMenuBtn.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });

        // Carousel functionality
        let currentSlide = 0;
        const slides = document.querySelectorAll('.carousel-slide');
        const indicators = document.querySelectorAll('.carousel-indicator');
        const totalSlides = slides.length;

        function showSlide(index) {
            slides.forEach(slide => slide.classList.remove('active'));
            indicators.forEach(indicator => indicator.classList.remove('bg-white'));
            slides[index].classList.add('active');
            indicators[index].classList.add('bg-white');
        }

        function nextSlide() {
            currentSlide = (currentSlide + 1) % totalSlides;
            showSlide(currentSlide);
        }

        function prevSlide() {
            currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
            showSlide(currentSlide);
        }

        document.getElementById('nextBtn').addEventListener('click', nextSlide);
        document.getElementById('prevBtn').addEventListener('click', prevSlide);

        indicators.forEach((indicator, index) => {
            indicator.addEventListener('click', () => {
                currentSlide = index;
                showSlide(currentSlide);
            });
        });

        let autoPlay = setInterval(nextSlide, 5000);

        const carouselContainer = document.querySelector('.carousel-container');
        carouselContainer.addEventListener('mouseenter', () => clearInterval(autoPlay));
        carouselContainer.addEventListener('mouseleave', () => {
            autoPlay = setInterval(nextSlide, 5000);
        });

        showSlide(0);

        // Scroll reveal animation
        const observerOptions = { threshold: 0.1, rootMargin: '0px 0px -50px 0px' };
        const revealElements = document.querySelectorAll('.scroll-reveal');
        const revealOnScroll = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('revealed');
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);
        revealElements.forEach(element => {
            revealOnScroll.observe(element);
        });

        function openModal(modalId) {
            document.getElementById(modalId).classList.add('show');
        }
        function closeModal(modalId) {
            document.getElementById(modalId).classList.remove('show');
        }
        window.onclick = function(event) {
            if (event.target.classList.contains('modal')) {
                event.target.classList.remove('show');
            }
        }
       
        let cart = [];

    function addToCart(id, name, price) {
      const existing = cart.find(i => i.id === id);
      if (existing) existing.quantity += 1;
      else cart.push({ id, name, price: Number(price), quantity: 1 });
      updateCartDisplay();
      showAddedToCartMessage(name);
    }

    function removeFromCart(id) {
      cart = cart.filter(i => i.id !== id);
      updateCartDisplay();
    }

    function updateQuantity(id, change) {
      const item = cart.find(i => i.id === id);
      if (!item) return;
      item.quantity += change;
      if (item.quantity <= 0) removeFromCart(id);
      else updateCartDisplay();
    }

    function updateCartDisplay() {
      const cartItems = document.getElementById('cartItems');
      const mobileCartItems = document.getElementById('mobileCartItems');
      const cartTotalEl = document.getElementById('cartTotal');
      const mobileCartTotalEl = document.getElementById('mobileCartTotal');
      const checkoutBtn = document.getElementById('checkoutBtn');
      const cartBadge = document.getElementById('cartBadge');

      if (cart.length === 0) {
        const empty = '<p class="text-amber-700 text-center py-8">Tu carrito está vacío</p>';
        cartItems.innerHTML = empty;
        mobileCartItems.innerHTML = '<p class="text-amber-700 text-center py-4">Tu carrito está vacío</p>';
        cartTotalEl.textContent = '$0.00';
        mobileCartTotalEl.textContent = '$0.00';
        checkoutBtn.disabled = true;
        cartBadge.classList.add('hidden');
        return;
      }

      let itemsHTML = '';
      let total = 0;

      cart.forEach(item => {
        const itemTotal = item.price * item.quantity;
        total += itemTotal;

        itemsHTML += `
          <div class="cart-item flex justify-between items-center p-3 bg-amber-50 rounded-lg">
            <div class="flex-1">
              <h4 class="font-semibold text-amber-800">${item.name}</h4>
              <p class="text-amber-600">$${item.price.toFixed(2)} c/u</p>
            </div>
            <div class="flex items-center space-x-2">
              <button onclick="updateQuantity(${JSON.stringify(item.id)}, -1)" class="bg-amber-200 text-amber-800 w-8 h-8 rounded-full hover:bg-amber-300 transition-colors">
                <i class="fas fa-minus text-xs"></i>
              </button>
              <span class="font-semibold text-amber-800 w-8 text-center">${item.quantity}</span>
              <button onclick="updateQuantity(${JSON.stringify(item.id)}, 1)" class="bg-amber-200 text-amber-800 w-8 h-8 rounded-full hover:bg-amber-300 transition-colors">
                <i class="fas fa-plus text-xs"></i>
              </button>
            </div>
            <div class="ml-4 text-right">
              <p class="font-bold text-amber-800">$${itemTotal.toFixed(2)}</p>
              <button onclick="removeFromCart(${JSON.stringify(item.id)})" class="text-red-500 hover:text-red-700 text-xs">
                <i class="fas fa-trash"></i>
              </button>
            </div>
          </div>
        `;
      });

      cartItems.innerHTML = itemsHTML;
      mobileCartItems.innerHTML = itemsHTML;
      cartTotalEl.textContent = `$${total.toFixed(2)}`;
      mobileCartTotalEl.textContent = `$${total.toFixed(2)}`;
      checkoutBtn.disabled = false;

      const totalItems = cart.reduce((s, i) => s + i.quantity, 0);
      cartBadge.textContent = totalItems;
      cartBadge.classList.remove('hidden');
    }

    function showAddedToCartMessage(productName) {
      const notif = document.createElement('div');
      notif.className = 'fixed top-20 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
      notif.innerHTML = `<i class="fas fa-check mr-2"></i>${productName} agregado al carrito`;
      document.body.appendChild(notif);
      setTimeout(() => notif.remove(), 2500);
    }

    function toggleMobileCart() {
      document.getElementById('mobileCartModal').classList.toggle('hidden');
    }

    function checkout() {
      if (cart.length === 0) return;
      alert(
        '¡Gracias por tu compra!\\n' +
        'Total: $' + cart.reduce((s, i) => s + (i.price * i.quantity), 0).toFixed(2) +
        '\\n\\nTu pedido será preparado en 15-20 minutos.'
      );
      cart = [];
      updateCartDisplay();
      document.getElementById('mobileCartModal').classList.add('hidden');
    }

    document.getElementById('mobileCartModal').addEventListener('click', function(e) {
      if (e.target === this) toggleMobileCart();
    });

    document.addEventListener('DOMContentLoaded', updateCartDisplay);

    document.getElementById('contactForm').addEventListener('submit', function(e) {
            e.preventDefault();
            alert('¡Gracias por tu mensaje! Te contactaremos pronto.');
            this.reset();
        });
          let currentTable = null;
        let currentOrder = [];
        let orderTotal = 0;

        function selectTable(tableNumber, status) {
            currentTable = tableNumber;
            document.getElementById('selectedTable').textContent = tableNumber;
            
            document.querySelectorAll('.table-available, .table-occupied').forEach(table => {
                table.classList.remove('table-selected');
            });
            event.currentTarget.classList.add('table-selected');
            
            document.getElementById('orderPanel').classList.add('show');
        }

        function closeOrderPanel() {
            document.getElementById('orderPanel').classList.remove('show');
        }

        function showCategory(category) {
            document.querySelectorAll('.menu-category').forEach(cat => cat.classList.add('hidden'));
            document.getElementById(category).classList.remove('hidden');
            
            document.querySelectorAll('.category-btn').forEach(btn => {
                btn.classList.remove('bg-amber-600', 'text-white');
                btn.classList.add('bg-amber-200', 'text-amber-800');
            });
            event.currentTarget.classList.remove('bg-amber-200', 'text-amber-800');
            event.currentTarget.classList.add('bg-amber-600', 'text-white');
        }

        function addToOrder(itemName, price) {
            const existingItem = currentOrder.find(item => item.name === itemName);
            
            if (existingItem) {
                existingItem.quantity += 1;
            } else {
                currentOrder.push({ name: itemName, price: price, quantity: 1 });
            }
            
            updateOrderDisplay();
        }

        function removeFromOrder(index) {
            currentOrder.splice(index, 1);
            updateOrderDisplay();
        }

        function updateOrderDisplay() {
            const orderContainer = document.getElementById('currentOrder');
            const totalElement = document.getElementById('orderTotal');
            
            if (currentOrder.length === 0) {
                orderContainer.innerHTML = '<p class="text-amber-600 text-sm">Selecciona productos del menú</p>';
                orderTotal = 0;
            } else {
                orderContainer.innerHTML = currentOrder.map((item, index) => `
                    <div class="flex justify-between items-center text-sm">
                        <span>${item.quantity}x ${item.name}</span>
                        <div class="flex items-center space-x-2">
                            <span>$${(item.price * item.quantity).toFixed(2)}</span>
                            <button onclick="removeFromOrder(${index})" class="text-red-500 hover:text-red-700">
                                <i class="fas fa-trash text-xs"></i>
                            </button>
                        </div>
                    </div>
                `).join('');
                
                orderTotal = currentOrder.reduce((total, item) => total + (item.price * item.quantity), 0);
            }
            
            totalElement.textContent = `$${orderTotal.toFixed(2)}`;
        }

        function submitOrder() {
            if (currentOrder.length === 0) {
                alert('Agrega productos a la orden primero');
                return;
            }
            
            alert(`Orden enviada para Mesa ${currentTable}\nTotal: $${orderTotal.toFixed(2)}`);
            currentOrder = [];
            updateOrderDisplay();
            closeOrderPanel();
        }

        // Initialize
        showCategory('cafe');
         
         const usuarioLogueado = {{ 'true' if session.get('usuario_id') else 'false' }};
        document.getElementById('pedidoBtn').addEventListener('click', function(e) {
            if (!usuarioLogueado) {
                e.preventDefault();
                alert('Debes iniciar sesión para poder hacer un pedido.');
            } else {
                window.location.href = "{{ url_for('pedidos.crear_pedido') }}";
            }
        });
    