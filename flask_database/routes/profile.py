from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db, get_mongo

profile = Blueprint('profile', __name__)

RECHARGE_OPTIONS = [10, 50, 100, 200, 500]


@profile.route('/profile')
@login_required
def view():
    # Fetch transaction history (last 50)
    transactions = list(get_mongo()['transactions'].find(
        {'user_id': current_user.id}
    ).sort('created_at', -1).limit(50))
    for t in transactions:
        t['_id'] = str(t['_id'])

    return render_template(
        'profile.html',
        recharge_options=RECHARGE_OPTIONS,
        transactions=transactions,
    )


@profile.route('/profile/recharge', methods=['POST'])
@login_required
def recharge():
    amount = request.form.get('amount', 0, type=float)
    if amount not in RECHARGE_OPTIONS:
        flash('无效的充值金额。', 'danger')
        return redirect(url_for('profile.view'))

    balance_after = float(current_user.balance or 0) + amount
    current_user.balance = balance_after
    db.session.commit()

    # Record recharge transaction
    get_mongo()['transactions'].insert_one({
        'user_id': current_user.id,
        'type': 'recharge',
        'amount': amount,
        'balance_after': balance_after,
        'created_at': datetime.utcnow(),
    })

    flash(f'充值成功！已到账 ¥{amount:.2f}，当前余额 ¥{balance_after:.2f}', 'success')
    return redirect(url_for('profile.view'))
