@app.route('/list-ordres')
def list_orders():
    orders = Order.query.all()
    app.logger.info("The page with the list of all orders has been loaded")
    return render_template('list_orders.html', orders=orders)