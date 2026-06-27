import React, { createContext, useState, useContext, useEffect } from 'react';

const CartContext = createContext();

export const CartProvider = ({ children }) => {
  const [cart, setCart] = useState(() => {
    try {
      const savedCart = localStorage.getItem('zt_cart');
      return savedCart ? JSON.parse(savedCart) : [];
    } catch {
      return [];
    }
  });

  // Save cart to local storage whenever it changes
  useEffect(() => {
    localStorage.setItem('zt_cart', JSON.stringify(cart));
  }, [cart]);

  const addToCart = (plan, billingCycle) => {
    setCart(prev => {
      const itemId = `${plan.id}-${billingCycle}`;
      const existing = prev.find(item => item.id === itemId);

      // Price calculation
      let price = plan.price[billingCycle];
      if (billingCycle === 'annual') {
        price = price * 12; // Annual pricing is shown monthly but billed annually
      }

      const itemName = `${plan.name} (${billingCycle === 'monthly' ? 'Monthly' : 'Annual'})`;

      if (existing) {
        return prev.map(item => 
          item.id === itemId 
            ? { ...item, quantity: item.quantity + 1 }
            : item
        );
      }

      return [
        ...prev, 
        { 
          id: itemId, 
          planId: plan.id,
          name: itemName, 
          price: price, 
          baseMonthlyPrice: plan.price[billingCycle],
          billingCycle: billingCycle,
          quantity: 1 
        }
      ];
    });
  };

  const removeFromCart = (itemId) => {
    setCart(prev => prev.filter(item => item.id !== itemId));
  };

  const updateQuantity = (itemId, qty) => {
    setCart(prev => 
      prev.map(item => 
        item.id === itemId 
          ? { ...item, quantity: Math.max(1, qty) }
          : item
      )
    );
  };

  const clearCart = () => {
    setCart([]);
  };

  const getCartTotal = () => {
    return cart.reduce((total, item) => total + (item.price * item.quantity), 0);
  };

  const getCartCount = () => {
    return cart.reduce((count, item) => count + item.quantity, 0);
  };

  return (
    <CartContext.Provider value={{ 
      cart, 
      addToCart, 
      removeFromCart, 
      updateQuantity, 
      clearCart, 
      getCartTotal,
      getCartCount
    }}>
      {children}
    </CartContext.Provider>
  );
};

export const useCart = () => useContext(CartContext);
