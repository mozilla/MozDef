//////////////////////////////////////////////////////////////////////////
//                                                                      //
// This is a generated file. You can view the original                  //
// source in your browser if your browser supports source maps.         //
//                                                                      //
// If you are using Chrome, open the Developer Tools and click the gear //
// icon in its lower right corner. In the General Settings panel, turn  //
// on 'Enable source maps'.                                             //
//                                                                      //
// If you are using Firefox 23, go to `about:config` and set the        //
// `devtools.debugger.source-maps-enabled` preference to true.          //
// (The preference should be on by default in Firefox 24; versions      //
// older than 23 do not support source maps.)                           //
//                                                                      //
//////////////////////////////////////////////////////////////////////////


(function () {

/* Imports */
var Meteor = Package.meteor.Meteor;
var $ = Package.jquery.$;
var jQuery = Package.jquery.jQuery;

(function () {

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                                  //
// packages/bootstrap/js/bootstrap.js                                                                               //
//                                                                                                                  //
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                                    //
/* ===================================================                                                              // 1
 * bootstrap-transition.js v2.3.0                                                                                   // 2
 * http://twitter.github.com/bootstrap/javascript.html#transitions                                                  // 3
 * ===================================================                                                              // 4
 * Copyright 2012 Twitter, Inc.                                                                                     // 5
 *                                                                                                                  // 6
 * Licensed under the Apache License, Version 2.0 (the "License");                                                  // 7
 * you may not use this file except in compliance with the License.                                                 // 8
 * You may obtain a copy of the License at                                                                          // 9
 *                                                                                                                  // 10
 * http://www.apache.org/licenses/LICENSE-2.0                                                                       // 11
 *                                                                                                                  // 12
 * Unless required by applicable law or agreed to in writing, software                                              // 13
 * distributed under the License is distributed on an "AS IS" BASIS,                                                // 14
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.                                         // 15
 * See the License for the specific language governing permissions and                                              // 16
 * limitations under the License.                                                                                   // 17
 * ========================================================== */                                                    // 18
                                                                                                                    // 19
                                                                                                                    // 20
!function ($) {                                                                                                     // 21
                                                                                                                    // 22
  "use strict"; // jshint ;_;                                                                                       // 23
                                                                                                                    // 24
                                                                                                                    // 25
  /* CSS TRANSITION SUPPORT (http://www.modernizr.com/)                                                             // 26
   * ======================================================= */                                                     // 27
                                                                                                                    // 28
  $(function () {                                                                                                   // 29
                                                                                                                    // 30
    $.support.transition = (function () {                                                                           // 31
                                                                                                                    // 32
      var transitionEnd = (function () {                                                                            // 33
                                                                                                                    // 34
        var el = document.createElement('bootstrap')                                                                // 35
          , transEndEventNames = {                                                                                  // 36
               'WebkitTransition' : 'webkitTransitionEnd'                                                           // 37
            ,  'MozTransition'    : 'transitionend'                                                                 // 38
            ,  'OTransition'      : 'oTransitionEnd otransitionend'                                                 // 39
            ,  'transition'       : 'transitionend'                                                                 // 40
            }                                                                                                       // 41
          , name                                                                                                    // 42
                                                                                                                    // 43
        for (name in transEndEventNames){                                                                           // 44
          if (el.style[name] !== undefined) {                                                                       // 45
            return transEndEventNames[name]                                                                         // 46
          }                                                                                                         // 47
        }                                                                                                           // 48
                                                                                                                    // 49
      }())                                                                                                          // 50
                                                                                                                    // 51
      return transitionEnd && {                                                                                     // 52
        end: transitionEnd                                                                                          // 53
      }                                                                                                             // 54
                                                                                                                    // 55
    })()                                                                                                            // 56
                                                                                                                    // 57
  })                                                                                                                // 58
                                                                                                                    // 59
}(window.jQuery);/* ==========================================================                                      // 60
 * bootstrap-alert.js v2.3.0                                                                                        // 61
 * http://twitter.github.com/bootstrap/javascript.html#alerts                                                       // 62
 * ==========================================================                                                       // 63
 * Copyright 2012 Twitter, Inc.                                                                                     // 64
 *                                                                                                                  // 65
 * Licensed under the Apache License, Version 2.0 (the "License");                                                  // 66
 * you may not use this file except in compliance with the License.                                                 // 67
 * You may obtain a copy of the License at                                                                          // 68
 *                                                                                                                  // 69
 * http://www.apache.org/licenses/LICENSE-2.0                                                                       // 70
 *                                                                                                                  // 71
 * Unless required by applicable law or agreed to in writing, software                                              // 72
 * distributed under the License is distributed on an "AS IS" BASIS,                                                // 73
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.                                         // 74
 * See the License for the specific language governing permissions and                                              // 75
 * limitations under the License.                                                                                   // 76
 * ========================================================== */                                                    // 77
                                                                                                                    // 78
                                                                                                                    // 79
!function ($) {                                                                                                     // 80
                                                                                                                    // 81
  "use strict"; // jshint ;_;                                                                                       // 82
                                                                                                                    // 83
                                                                                                                    // 84
 /* ALERT CLASS DEFINITION                                                                                          // 85
  * ====================== */                                                                                       // 86
                                                                                                                    // 87
  var dismiss = '[data-dismiss="alert"]'                                                                            // 88
    , Alert = function (el) {                                                                                       // 89
        $(el).on('click', dismiss, this.close)                                                                      // 90
      }                                                                                                             // 91
                                                                                                                    // 92
  Alert.prototype.close = function (e) {                                                                            // 93
    var $this = $(this)                                                                                             // 94
      , selector = $this.attr('data-target')                                                                        // 95
      , $parent                                                                                                     // 96
                                                                                                                    // 97
    if (!selector) {                                                                                                // 98
      selector = $this.attr('href')                                                                                 // 99
      selector = selector && selector.replace(/.*(?=#[^\s]*$)/, '') //strip for ie7                                 // 100
    }                                                                                                               // 101
                                                                                                                    // 102
    $parent = $(selector)                                                                                           // 103
                                                                                                                    // 104
    e && e.preventDefault()                                                                                         // 105
                                                                                                                    // 106
    $parent.length || ($parent = $this.hasClass('alert') ? $this : $this.parent())                                  // 107
                                                                                                                    // 108
    $parent.trigger(e = $.Event('close'))                                                                           // 109
                                                                                                                    // 110
    if (e.isDefaultPrevented()) return                                                                              // 111
                                                                                                                    // 112
    $parent.removeClass('in')                                                                                       // 113
                                                                                                                    // 114
    function removeElement() {                                                                                      // 115
      $parent                                                                                                       // 116
        .trigger('closed')                                                                                          // 117
        .remove()                                                                                                   // 118
    }                                                                                                               // 119
                                                                                                                    // 120
    $.support.transition && $parent.hasClass('fade') ?                                                              // 121
      $parent.on($.support.transition.end, removeElement) :                                                         // 122
      removeElement()                                                                                               // 123
  }                                                                                                                 // 124
                                                                                                                    // 125
                                                                                                                    // 126
 /* ALERT PLUGIN DEFINITION                                                                                         // 127
  * ======================= */                                                                                      // 128
                                                                                                                    // 129
  var old = $.fn.alert                                                                                              // 130
                                                                                                                    // 131
  $.fn.alert = function (option) {                                                                                  // 132
    return this.each(function () {                                                                                  // 133
      var $this = $(this)                                                                                           // 134
        , data = $this.data('alert')                                                                                // 135
      if (!data) $this.data('alert', (data = new Alert(this)))                                                      // 136
      if (typeof option == 'string') data[option].call($this)                                                       // 137
    })                                                                                                              // 138
  }                                                                                                                 // 139
                                                                                                                    // 140
  $.fn.alert.Constructor = Alert                                                                                    // 141
                                                                                                                    // 142
                                                                                                                    // 143
 /* ALERT NO CONFLICT                                                                                               // 144
  * ================= */                                                                                            // 145
                                                                                                                    // 146
  $.fn.alert.noConflict = function () {                                                                             // 147
    $.fn.alert = old                                                                                                // 148
    return this                                                                                                     // 149
  }                                                                                                                 // 150
                                                                                                                    // 151
                                                                                                                    // 152
 /* ALERT DATA-API                                                                                                  // 153
  * ============== */                                                                                               // 154
                                                                                                                    // 155
  $(document).on('click.alert.data-api', dismiss, Alert.prototype.close)                                            // 156
                                                                                                                    // 157
}(window.jQuery);/* ============================================================                                    // 158
 * bootstrap-button.js v2.3.0                                                                                       // 159
 * http://twitter.github.com/bootstrap/javascript.html#buttons                                                      // 160
 * ============================================================                                                     // 161
 * Copyright 2012 Twitter, Inc.                                                                                     // 162
 *                                                                                                                  // 163
 * Licensed under the Apache License, Version 2.0 (the "License");                                                  // 164
 * you may not use this file except in compliance with the License.                                                 // 165
 * You may obtain a copy of the License at                                                                          // 166
 *                                                                                                                  // 167
 * http://www.apache.org/licenses/LICENSE-2.0                                                                       // 168
 *                                                                                                                  // 169
 * Unless required by applicable law or agreed to in writing, software                                              // 170
 * distributed under the License is distributed on an "AS IS" BASIS,                                                // 171
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.                                         // 172
 * See the License for the specific language governing permissions and                                              // 173
 * limitations under the License.                                                                                   // 174
 * ============================================================ */                                                  // 175
                                                                                                                    // 176
                                                                                                                    // 177
!function ($) {                                                                                                     // 178
                                                                                                                    // 179
  "use strict"; // jshint ;_;                                                                                       // 180
                                                                                                                    // 181
                                                                                                                    // 182
 /* BUTTON PUBLIC CLASS DEFINITION                                                                                  // 183
  * ============================== */                                                                               // 184
                                                                                                                    // 185
  var Button = function (element, options) {                                                                        // 186
    this.$element = $(element)                                                                                      // 187
    this.options = $.extend({}, $.fn.button.defaults, options)                                                      // 188
  }                                                                                                                 // 189
                                                                                                                    // 190
  Button.prototype.setState = function (state) {                                                                    // 191
    var d = 'disabled'                                                                                              // 192
      , $el = this.$element                                                                                         // 193
      , data = $el.data()                                                                                           // 194
      , val = $el.is('input') ? 'val' : 'html'                                                                      // 195
                                                                                                                    // 196
    state = state + 'Text'                                                                                          // 197
    data.resetText || $el.data('resetText', $el[val]())                                                             // 198
                                                                                                                    // 199
    $el[val](data[state] || this.options[state])                                                                    // 200
                                                                                                                    // 201
    // push to event loop to allow forms to submit                                                                  // 202
    setTimeout(function () {                                                                                        // 203
      state == 'loadingText' ?                                                                                      // 204
        $el.addClass(d).attr(d, d) :                                                                                // 205
        $el.removeClass(d).removeAttr(d)                                                                            // 206
    }, 0)                                                                                                           // 207
  }                                                                                                                 // 208
                                                                                                                    // 209
  Button.prototype.toggle = function () {                                                                           // 210
    var $parent = this.$element.closest('[data-toggle="buttons-radio"]')                                            // 211
                                                                                                                    // 212
    $parent && $parent                                                                                              // 213
      .find('.active')                                                                                              // 214
      .removeClass('active')                                                                                        // 215
                                                                                                                    // 216
    this.$element.toggleClass('active')                                                                             // 217
  }                                                                                                                 // 218
                                                                                                                    // 219
                                                                                                                    // 220
 /* BUTTON PLUGIN DEFINITION                                                                                        // 221
  * ======================== */                                                                                     // 222
                                                                                                                    // 223
  var old = $.fn.button                                                                                             // 224
                                                                                                                    // 225
  $.fn.button = function (option) {                                                                                 // 226
    return this.each(function () {                                                                                  // 227
      var $this = $(this)                                                                                           // 228
        , data = $this.data('button')                                                                               // 229
        , options = typeof option == 'object' && option                                                             // 230
      if (!data) $this.data('button', (data = new Button(this, options)))                                           // 231
      if (option == 'toggle') data.toggle()                                                                         // 232
      else if (option) data.setState(option)                                                                        // 233
    })                                                                                                              // 234
  }                                                                                                                 // 235
                                                                                                                    // 236
  $.fn.button.defaults = {                                                                                          // 237
    loadingText: 'loading...'                                                                                       // 238
  }                                                                                                                 // 239
                                                                                                                    // 240
  $.fn.button.Constructor = Button                                                                                  // 241
                                                                                                                    // 242
                                                                                                                    // 243
 /* BUTTON NO CONFLICT                                                                                              // 244
  * ================== */                                                                                           // 245
                                                                                                                    // 246
  $.fn.button.noConflict = function () {                                                                            // 247
    $.fn.button = old                                                                                               // 248
    return this                                                                                                     // 249
  }                                                                                                                 // 250
                                                                                                                    // 251
                                                                                                                    // 252
 /* BUTTON DATA-API                                                                                                 // 253
  * =============== */                                                                                              // 254
                                                                                                                    // 255
  $(document).on('click.button.data-api', '[data-toggle^=button]', function (e) {                                   // 256
    var $btn = $(e.target)                                                                                          // 257
    if (!$btn.hasClass('btn')) $btn = $btn.closest('.btn')                                                          // 258
    $btn.button('toggle')                                                                                           // 259
  })                                                                                                                // 260
                                                                                                                    // 261
}(window.jQuery);/* ==========================================================                                      // 262
 * bootstrap-carousel.js v2.3.0                                                                                     // 263
 * http://twitter.github.com/bootstrap/javascript.html#carousel                                                     // 264
 * ==========================================================                                                       // 265
 * Copyright 2012 Twitter, Inc.                                                                                     // 266
 *                                                                                                                  // 267
 * Licensed under the Apache License, Version 2.0 (the "License");                                                  // 268
 * you may not use this file except in compliance with the License.                                                 // 269
 * You may obtain a copy of the License at                                                                          // 270
 *                                                                                                                  // 271
 * http://www.apache.org/licenses/LICENSE-2.0                                                                       // 272
 *                                                                                                                  // 273
 * Unless required by applicable law or agreed to in writing, software                                              // 274
 * distributed under the License is distributed on an "AS IS" BASIS,                                                // 275
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.                                         // 276
 * See the License for the specific language governing permissions and                                              // 277
 * limitations under the License.                                                                                   // 278
 * ========================================================== */                                                    // 279
                                                                                                                    // 280
                                                                                                                    // 281
!function ($) {                                                                                                     // 282
                                                                                                                    // 283
  "use strict"; // jshint ;_;                                                                                       // 284
                                                                                                                    // 285
                                                                                                                    // 286
 /* CAROUSEL CLASS DEFINITION                                                                                       // 287
  * ========================= */                                                                                    // 288
                                                                                                                    // 289
  var Carousel = function (element, options) {                                                                      // 290
    this.$element = $(element)                                                                                      // 291
    this.$indicators = this.$element.find('.carousel-indicators')                                                   // 292
    this.options = options                                                                                          // 293
    this.options.pause == 'hover' && this.$element                                                                  // 294
      .on('mouseenter', $.proxy(this.pause, this))                                                                  // 295
      .on('mouseleave', $.proxy(this.cycle, this))                                                                  // 296
  }                                                                                                                 // 297
                                                                                                                    // 298
  Carousel.prototype = {                                                                                            // 299
                                                                                                                    // 300
    cycle: function (e) {                                                                                           // 301
      if (!e) this.paused = false                                                                                   // 302
      if (this.interval) clearInterval(this.interval);                                                              // 303
      this.options.interval                                                                                         // 304
        && !this.paused                                                                                             // 305
        && (this.interval = setInterval($.proxy(this.next, this), this.options.interval))                           // 306
      return this                                                                                                   // 307
    }                                                                                                               // 308
                                                                                                                    // 309
  , getActiveIndex: function () {                                                                                   // 310
      this.$active = this.$element.find('.item.active')                                                             // 311
      this.$items = this.$active.parent().children()                                                                // 312
      return this.$items.index(this.$active)                                                                        // 313
    }                                                                                                               // 314
                                                                                                                    // 315
  , to: function (pos) {                                                                                            // 316
      var activeIndex = this.getActiveIndex()                                                                       // 317
        , that = this                                                                                               // 318
                                                                                                                    // 319
      if (pos > (this.$items.length - 1) || pos < 0) return                                                         // 320
                                                                                                                    // 321
      if (this.sliding) {                                                                                           // 322
        return this.$element.one('slid', function () {                                                              // 323
          that.to(pos)                                                                                              // 324
        })                                                                                                          // 325
      }                                                                                                             // 326
                                                                                                                    // 327
      if (activeIndex == pos) {                                                                                     // 328
        return this.pause().cycle()                                                                                 // 329
      }                                                                                                             // 330
                                                                                                                    // 331
      return this.slide(pos > activeIndex ? 'next' : 'prev', $(this.$items[pos]))                                   // 332
    }                                                                                                               // 333
                                                                                                                    // 334
  , pause: function (e) {                                                                                           // 335
      if (!e) this.paused = true                                                                                    // 336
      if (this.$element.find('.next, .prev').length && $.support.transition.end) {                                  // 337
        this.$element.trigger($.support.transition.end)                                                             // 338
        this.cycle()                                                                                                // 339
      }                                                                                                             // 340
      clearInterval(this.interval)                                                                                  // 341
      this.interval = null                                                                                          // 342
      return this                                                                                                   // 343
    }                                                                                                               // 344
                                                                                                                    // 345
  , next: function () {                                                                                             // 346
      if (this.sliding) return                                                                                      // 347
      return this.slide('next')                                                                                     // 348
    }                                                                                                               // 349
                                                                                                                    // 350
  , prev: function () {                                                                                             // 351
      if (this.sliding) return                                                                                      // 352
      return this.slide('prev')                                                                                     // 353
    }                                                                                                               // 354
                                                                                                                    // 355
  , slide: function (type, next) {                                                                                  // 356
      var $active = this.$element.find('.item.active')                                                              // 357
        , $next = next || $active[type]()                                                                           // 358
        , isCycling = this.interval                                                                                 // 359
        , direction = type == 'next' ? 'left' : 'right'                                                             // 360
        , fallback  = type == 'next' ? 'first' : 'last'                                                             // 361
        , that = this                                                                                               // 362
        , e                                                                                                         // 363
                                                                                                                    // 364
      this.sliding = true                                                                                           // 365
                                                                                                                    // 366
      isCycling && this.pause()                                                                                     // 367
                                                                                                                    // 368
      $next = $next.length ? $next : this.$element.find('.item')[fallback]()                                        // 369
                                                                                                                    // 370
      e = $.Event('slide', {                                                                                        // 371
        relatedTarget: $next[0]                                                                                     // 372
      , direction: direction                                                                                        // 373
      })                                                                                                            // 374
                                                                                                                    // 375
      if ($next.hasClass('active')) return                                                                          // 376
                                                                                                                    // 377
      if (this.$indicators.length) {                                                                                // 378
        this.$indicators.find('.active').removeClass('active')                                                      // 379
        this.$element.one('slid', function () {                                                                     // 380
          var $nextIndicator = $(that.$indicators.children()[that.getActiveIndex()])                                // 381
          $nextIndicator && $nextIndicator.addClass('active')                                                       // 382
        })                                                                                                          // 383
      }                                                                                                             // 384
                                                                                                                    // 385
      if ($.support.transition && this.$element.hasClass('slide')) {                                                // 386
        this.$element.trigger(e)                                                                                    // 387
        if (e.isDefaultPrevented()) return                                                                          // 388
        $next.addClass(type)                                                                                        // 389
        $next[0].offsetWidth // force reflow                                                                        // 390
        $active.addClass(direction)                                                                                 // 391
        $next.addClass(direction)                                                                                   // 392
        this.$element.one($.support.transition.end, function () {                                                   // 393
          $next.removeClass([type, direction].join(' ')).addClass('active')                                         // 394
          $active.removeClass(['active', direction].join(' '))                                                      // 395
          that.sliding = false                                                                                      // 396
          setTimeout(function () { that.$element.trigger('slid') }, 0)                                              // 397
        })                                                                                                          // 398
      } else {                                                                                                      // 399
        this.$element.trigger(e)                                                                                    // 400
        if (e.isDefaultPrevented()) return                                                                          // 401
        $active.removeClass('active')                                                                               // 402
        $next.addClass('active')                                                                                    // 403
        this.sliding = false                                                                                        // 404
        this.$element.trigger('slid')                                                                               // 405
      }                                                                                                             // 406
                                                                                                                    // 407
      isCycling && this.cycle()                                                                                     // 408
                                                                                                                    // 409
      return this                                                                                                   // 410
    }                                                                                                               // 411
                                                                                                                    // 412
  }                                                                                                                 // 413
                                                                                                                    // 414
                                                                                                                    // 415
 /* CAROUSEL PLUGIN DEFINITION                                                                                      // 416
  * ========================== */                                                                                   // 417
                                                                                                                    // 418
  var old = $.fn.carousel                                                                                           // 419
                                                                                                                    // 420
  $.fn.carousel = function (option) {                                                                               // 421
    return this.each(function () {                                                                                  // 422
      var $this = $(this)                                                                                           // 423
        , data = $this.data('carousel')                                                                             // 424
        , options = $.extend({}, $.fn.carousel.defaults, typeof option == 'object' && option)                       // 425
        , action = typeof option == 'string' ? option : options.slide                                               // 426
      if (!data) $this.data('carousel', (data = new Carousel(this, options)))                                       // 427
      if (typeof option == 'number') data.to(option)                                                                // 428
      else if (action) data[action]()                                                                               // 429
      else if (options.interval) data.pause().cycle()                                                               // 430
    })                                                                                                              // 431
  }                                                                                                                 // 432
                                                                                                                    // 433
  $.fn.carousel.defaults = {                                                                                        // 434
    interval: 5000                                                                                                  // 435
  , pause: 'hover'                                                                                                  // 436
  }                                                                                                                 // 437
                                                                                                                    // 438
  $.fn.carousel.Constructor = Carousel                                                                              // 439
                                                                                                                    // 440
                                                                                                                    // 441
 /* CAROUSEL NO CONFLICT                                                                                            // 442
  * ==================== */                                                                                         // 443
                                                                                                                    // 444
  $.fn.carousel.noConflict = function () {                                                                          // 445
    $.fn.carousel = old                                                                                             // 446
    return this                                                                                                     // 447
  }                                                                                                                 // 448
                                                                                                                    // 449
 /* CAROUSEL DATA-API                                                                                               // 450
  * ================= */                                                                                            // 451
                                                                                                                    // 452
  $(document).on('click.carousel.data-api', '[data-slide], [data-slide-to]', function (e) {                         // 453
    var $this = $(this), href                                                                                       // 454
      , $target = $($this.attr('data-target') || (href = $this.attr('href')) && href.replace(/.*(?=#[^\s]+$)/, '')) //strip for ie7
      , options = $.extend({}, $target.data(), $this.data())                                                        // 456
      , slideIndex                                                                                                  // 457
                                                                                                                    // 458
    $target.carousel(options)                                                                                       // 459
                                                                                                                    // 460
    if (slideIndex = $this.attr('data-slide-to')) {                                                                 // 461
      $target.data('carousel').pause().to(slideIndex).cycle()                                                       // 462
    }                                                                                                               // 463
                                                                                                                    // 464
    e.preventDefault()                                                                                              // 465
  })                                                                                                                // 466
                                                                                                                    // 467
}(window.jQuery);/* =============================================================                                   // 468
 * bootstrap-collapse.js v2.3.0                                                                                     // 469
 * http://twitter.github.com/bootstrap/javascript.html#collapse                                                     // 470
 * =============================================================                                                    // 471
 * Copyright 2012 Twitter, Inc.                                                                                     // 472
 *                                                                                                                  // 473
 * Licensed under the Apache License, Version 2.0 (the "License");                                                  // 474
 * you may not use this file except in compliance with the License.                                                 // 475
 * You may obtain a copy of the License at                                                                          // 476
 *                                                                                                                  // 477
 * http://www.apache.org/licenses/LICENSE-2.0                                                                       // 478
 *                                                                                                                  // 479
 * Unless required by applicable law or agreed to in writing, software                                              // 480
 * distributed under the License is distributed on an "AS IS" BASIS,                                                // 481
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.                                         // 482
 * See the License for the specific language governing permissions and                                              // 483
 * limitations under the License.                                                                                   // 484
 * ============================================================ */                                                  // 485
                                                                                                                    // 486
                                                                                                                    // 487
!function ($) {                                                                                                     // 488
                                                                                                                    // 489
  "use strict"; // jshint ;_;                                                                                       // 490
                                                                                                                    // 491
                                                                                                                    // 492
 /* COLLAPSE PUBLIC CLASS DEFINITION                                                                                // 493
  * ================================ */                                                                             // 494
                                                                                                                    // 495
  var Collapse = function (element, options) {                                                                      // 496
    this.$element = $(element)                                                                                      // 497
    this.options = $.extend({}, $.fn.collapse.defaults, options)                                                    // 498
                                                                                                                    // 499
    if (this.options.parent) {                                                                                      // 500
      this.$parent = $(this.options.parent)                                                                         // 501
    }                                                                                                               // 502
                                                                                                                    // 503
    this.options.toggle && this.toggle()                                                                            // 504
  }                                                                                                                 // 505
                                                                                                                    // 506
  Collapse.prototype = {                                                                                            // 507
                                                                                                                    // 508
    constructor: Collapse                                                                                           // 509
                                                                                                                    // 510
  , dimension: function () {                                                                                        // 511
      var hasWidth = this.$element.hasClass('width')                                                                // 512
      return hasWidth ? 'width' : 'height'                                                                          // 513
    }                                                                                                               // 514
                                                                                                                    // 515
  , show: function () {                                                                                             // 516
      var dimension                                                                                                 // 517
        , scroll                                                                                                    // 518
        , actives                                                                                                   // 519
        , hasData                                                                                                   // 520
                                                                                                                    // 521
      if (this.transitioning || this.$element.hasClass('in')) return                                                // 522
                                                                                                                    // 523
      dimension = this.dimension()                                                                                  // 524
      scroll = $.camelCase(['scroll', dimension].join('-'))                                                         // 525
      actives = this.$parent && this.$parent.find('> .accordion-group > .in')                                       // 526
                                                                                                                    // 527
      if (actives && actives.length) {                                                                              // 528
        hasData = actives.data('collapse')                                                                          // 529
        if (hasData && hasData.transitioning) return                                                                // 530
        actives.collapse('hide')                                                                                    // 531
        hasData || actives.data('collapse', null)                                                                   // 532
      }                                                                                                             // 533
                                                                                                                    // 534
      this.$element[dimension](0)                                                                                   // 535
      this.transition('addClass', $.Event('show'), 'shown')                                                         // 536
      $.support.transition && this.$element[dimension](this.$element[0][scroll])                                    // 537
    }                                                                                                               // 538
                                                                                                                    // 539
  , hide: function () {                                                                                             // 540
      var dimension                                                                                                 // 541
      if (this.transitioning || !this.$element.hasClass('in')) return                                               // 542
      dimension = this.dimension()                                                                                  // 543
      this.reset(this.$element[dimension]())                                                                        // 544
      this.transition('removeClass', $.Event('hide'), 'hidden')                                                     // 545
      this.$element[dimension](0)                                                                                   // 546
    }                                                                                                               // 547
                                                                                                                    // 548
  , reset: function (size) {                                                                                        // 549
      var dimension = this.dimension()                                                                              // 550
                                                                                                                    // 551
      this.$element                                                                                                 // 552
        .removeClass('collapse')                                                                                    // 553
        [dimension](size || 'auto')                                                                                 // 554
        [0].offsetWidth                                                                                             // 555
                                                                                                                    // 556
      this.$element[size !== null ? 'addClass' : 'removeClass']('collapse')                                         // 557
                                                                                                                    // 558
      return this                                                                                                   // 559
    }                                                                                                               // 560
                                                                                                                    // 561
  , transition: function (method, startEvent, completeEvent) {                                                      // 562
      var that = this                                                                                               // 563
        , complete = function () {                                                                                  // 564
            if (startEvent.type == 'show') that.reset()                                                             // 565
            that.transitioning = 0                                                                                  // 566
            that.$element.trigger(completeEvent)                                                                    // 567
          }                                                                                                         // 568
                                                                                                                    // 569
      this.$element.trigger(startEvent)                                                                             // 570
                                                                                                                    // 571
      if (startEvent.isDefaultPrevented()) return                                                                   // 572
                                                                                                                    // 573
      this.transitioning = 1                                                                                        // 574
                                                                                                                    // 575
      this.$element[method]('in')                                                                                   // 576
                                                                                                                    // 577
      $.support.transition && this.$element.hasClass('collapse') ?                                                  // 578
        this.$element.one($.support.transition.end, complete) :                                                     // 579
        complete()                                                                                                  // 580
    }                                                                                                               // 581
                                                                                                                    // 582
  , toggle: function () {                                                                                           // 583
      this[this.$element.hasClass('in') ? 'hide' : 'show']()                                                        // 584
    }                                                                                                               // 585
                                                                                                                    // 586
  }                                                                                                                 // 587
                                                                                                                    // 588
                                                                                                                    // 589
 /* COLLAPSE PLUGIN DEFINITION                                                                                      // 590
  * ========================== */                                                                                   // 591
                                                                                                                    // 592
  var old = $.fn.collapse                                                                                           // 593
                                                                                                                    // 594
  $.fn.collapse = function (option) {                                                                               // 595
    return this.each(function () {                                                                                  // 596
      var $this = $(this)                                                                                           // 597
        , data = $this.data('collapse')                                                                             // 598
        , options = $.extend({}, $.fn.collapse.defaults, $this.data(), typeof option == 'object' && option)         // 599
      if (!data) $this.data('collapse', (data = new Collapse(this, options)))                                       // 600
      if (typeof option == 'string') data[option]()                                                                 // 601
    })                                                                                                              // 602
  }                                                                                                                 // 603
                                                                                                                    // 604
  $.fn.collapse.defaults = {                                                                                        // 605
    toggle: true                                                                                                    // 606
  }                                                                                                                 // 607
                                                                                                                    // 608
  $.fn.collapse.Constructor = Collapse                                                                              // 609
                                                                                                                    // 610
                                                                                                                    // 611
 /* COLLAPSE NO CONFLICT                                                                                            // 612
  * ==================== */                                                                                         // 613
                                                                                                                    // 614
  $.fn.collapse.noConflict = function () {                                                                          // 615
    $.fn.collapse = old                                                                                             // 616
    return this                                                                                                     // 617
  }                                                                                                                 // 618
                                                                                                                    // 619
                                                                                                                    // 620
 /* COLLAPSE DATA-API                                                                                               // 621
  * ================= */                                                                                            // 622
                                                                                                                    // 623
  $(document).on('click.collapse.data-api', '[data-toggle=collapse]', function (e) {                                // 624
    var $this = $(this), href                                                                                       // 625
      , target = $this.attr('data-target')                                                                          // 626
        || e.preventDefault()                                                                                       // 627
        || (href = $this.attr('href')) && href.replace(/.*(?=#[^\s]+$)/, '') //strip for ie7                        // 628
      , option = $(target).data('collapse') ? 'toggle' : $this.data()                                               // 629
    $this[$(target).hasClass('in') ? 'addClass' : 'removeClass']('collapsed')                                       // 630
    $(target).collapse(option)                                                                                      // 631
  })                                                                                                                // 632
                                                                                                                    // 633
}(window.jQuery);/* ============================================================                                    // 634
 * bootstrap-dropdown.js v2.3.0                                                                                     // 635
 * http://twitter.github.com/bootstrap/javascript.html#dropdowns                                                    // 636
 * ============================================================                                                     // 637
 * Copyright 2012 Twitter, Inc.                                                                                     // 638
 *                                                                                                                  // 639
 * Licensed under the Apache License, Version 2.0 (the "License");                                                  // 640
 * you may not use this file except in compliance with the License.                                                 // 641
 * You may obtain a copy of the License at                                                                          // 642
 *                                                                                                                  // 643
 * http://www.apache.org/licenses/LICENSE-2.0                                                                       // 644
 *                                                                                                                  // 645
 * Unless required by applicable law or agreed to in writing, software                                              // 646
 * distributed under the License is distributed on an "AS IS" BASIS,                                                // 647
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.                                         // 648
 * See the License for the specific language governing permissions and                                              // 649
 * limitations under the License.                                                                                   // 650
 * ============================================================ */                                                  // 651
                                                                                                                    // 652
                                                                                                                    // 653
!function ($) {                                                                                                     // 654
                                                                                                                    // 655
  "use strict"; // jshint ;_;                                                                                       // 656
                                                                                                                    // 657
                                                                                                                    // 658
 /* DROPDOWN CLASS DEFINITION                                                                                       // 659
  * ========================= */                                                                                    // 660
                                                                                                                    // 661
  var toggle = '[data-toggle=dropdown]'                                                                             // 662
    , Dropdown = function (element) {                                                                               // 663
        var $el = $(element).on('click.dropdown.data-api', this.toggle)                                             // 664
        $('html').on('click.dropdown.data-api', function () {                                                       // 665
          $el.parent().removeClass('open')                                                                          // 666
        })                                                                                                          // 667
      }                                                                                                             // 668
                                                                                                                    // 669
  Dropdown.prototype = {                                                                                            // 670
                                                                                                                    // 671
    constructor: Dropdown                                                                                           // 672
                                                                                                                    // 673
  , toggle: function (e) {                                                                                          // 674
      var $this = $(this)                                                                                           // 675
        , $parent                                                                                                   // 676
        , isActive                                                                                                  // 677
                                                                                                                    // 678
      if ($this.is('.disabled, :disabled')) return                                                                  // 679
                                                                                                                    // 680
      $parent = getParent($this)                                                                                    // 681
                                                                                                                    // 682
      isActive = $parent.hasClass('open')                                                                           // 683
                                                                                                                    // 684
      clearMenus()                                                                                                  // 685
                                                                                                                    // 686
      if (!isActive) {                                                                                              // 687
        $parent.toggleClass('open')                                                                                 // 688
      }                                                                                                             // 689
                                                                                                                    // 690
      $this.focus()                                                                                                 // 691
                                                                                                                    // 692
      return false                                                                                                  // 693
    }                                                                                                               // 694
                                                                                                                    // 695
  , keydown: function (e) {                                                                                         // 696
      var $this                                                                                                     // 697
        , $items                                                                                                    // 698
        , $active                                                                                                   // 699
        , $parent                                                                                                   // 700
        , isActive                                                                                                  // 701
        , index                                                                                                     // 702
                                                                                                                    // 703
      if (!/(38|40|27)/.test(e.keyCode)) return                                                                     // 704
                                                                                                                    // 705
      $this = $(this)                                                                                               // 706
                                                                                                                    // 707
      e.preventDefault()                                                                                            // 708
      e.stopPropagation()                                                                                           // 709
                                                                                                                    // 710
      if ($this.is('.disabled, :disabled')) return                                                                  // 711
                                                                                                                    // 712
      $parent = getParent($this)                                                                                    // 713
                                                                                                                    // 714
      isActive = $parent.hasClass('open')                                                                           // 715
                                                                                                                    // 716
      if (!isActive || (isActive && e.keyCode == 27)) {                                                             // 717
        if (e.which == 27) $parent.find(toggle).focus()                                                             // 718
        return $this.click()                                                                                        // 719
      }                                                                                                             // 720
                                                                                                                    // 721
      $items = $('[role=menu] li:not(.divider):visible a', $parent)                                                 // 722
                                                                                                                    // 723
      if (!$items.length) return                                                                                    // 724
                                                                                                                    // 725
      index = $items.index($items.filter(':focus'))                                                                 // 726
                                                                                                                    // 727
      if (e.keyCode == 38 && index > 0) index--                                        // up                        // 728
      if (e.keyCode == 40 && index < $items.length - 1) index++                        // down                      // 729
      if (!~index) index = 0                                                                                        // 730
                                                                                                                    // 731
      $items                                                                                                        // 732
        .eq(index)                                                                                                  // 733
        .focus()                                                                                                    // 734
    }                                                                                                               // 735
                                                                                                                    // 736
  }                                                                                                                 // 737
                                                                                                                    // 738
  function clearMenus() {                                                                                           // 739
    $(toggle).each(function () {                                                                                    // 740
      getParent($(this)).removeClass('open')                                                                        // 741
    })                                                                                                              // 742
  }                                                                                                                 // 743
                                                                                                                    // 744
  function getParent($this) {                                                                                       // 745
    var selector = $this.attr('data-target')                                                                        // 746
      , $parent                                                                                                     // 747
                                                                                                                    // 748
    if (!selector) {                                                                                                // 749
      selector = $this.attr('href')                                                                                 // 750
      selector = selector && /#/.test(selector) && selector.replace(/.*(?=#[^\s]*$)/, '') //strip for ie7           // 751
    }                                                                                                               // 752
                                                                                                                    // 753
    $parent = selector && $(selector)                                                                               // 754
                                                                                                                    // 755
    if (!$parent || !$parent.length) $parent = $this.parent()                                                       // 756
                                                                                                                    // 757
    return $parent                                                                                                  // 758
  }                                                                                                                 // 759
                                                                                                                    // 760
                                                                                                                    // 761
  /* DROPDOWN PLUGIN DEFINITION                                                                                     // 762
   * ========================== */                                                                                  // 763
                                                                                                                    // 764
  var old = $.fn.dropdown                                                                                           // 765
                                                                                                                    // 766
  $.fn.dropdown = function (option) {                                                                               // 767
    return this.each(function () {                                                                                  // 768
      var $this = $(this)                                                                                           // 769
        , data = $this.data('dropdown')                                                                             // 770
      if (!data) $this.data('dropdown', (data = new Dropdown(this)))                                                // 771
      if (typeof option == 'string') data[option].call($this)                                                       // 772
    })                                                                                                              // 773
  }                                                                                                                 // 774
                                                                                                                    // 775
  $.fn.dropdown.Constructor = Dropdown                                                                              // 776
                                                                                                                    // 777
                                                                                                                    // 778
 /* DROPDOWN NO CONFLICT                                                                                            // 779
  * ==================== */                                                                                         // 780
                                                                                                                    // 781
  $.fn.dropdown.noConflict = function () {                                                                          // 782
    $.fn.dropdown = old                                                                                             // 783
    return this                                                                                                     // 784
  }                                                                                                                 // 785
                                                                                                                    // 786
                                                                                                                    // 787
  /* APPLY TO STANDARD DROPDOWN ELEMENTS                                                                            // 788
   * =================================== */                                                                         // 789
                                                                                                                    // 790
  $(document)                                                                                                       // 791
    .on('click.dropdown.data-api', clearMenus)                                                                      // 792
    .on('click.dropdown.data-api', '.dropdown form', function (e) { e.stopPropagation() })                          // 793
    .on('.dropdown-menu', function (e) { e.stopPropagation() })                                                     // 794
    .on('click.dropdown.data-api'  , toggle, Dropdown.prototype.toggle)                                             // 795
    .on('keydown.dropdown.data-api', toggle + ', [role=menu]' , Dropdown.prototype.keydown)                         // 796
                                                                                                                    // 797
}(window.jQuery);                                                                                                   // 798
/* =========================================================                                                        // 799
 * bootstrap-modal.js v2.3.0                                                                                        // 800
 * http://twitter.github.com/bootstrap/javascript.html#modals                                                       // 801
 * =========================================================                                                        // 802
 * Copyright 2012 Twitter, Inc.                                                                                     // 803
 *                                                                                                                  // 804
 * Licensed under the Apache License, Version 2.0 (the "License");                                                  // 805
 * you may not use this file except in compliance with the License.                                                 // 806
 * You may obtain a copy of the License at                                                                          // 807
 *                                                                                                                  // 808
 * http://www.apache.org/licenses/LICENSE-2.0                                                                       // 809
 *                                                                                                                  // 810
 * Unless required by applicable law or agreed to in writing, software                                              // 811
 * distributed under the License is distributed on an "AS IS" BASIS,                                                // 812
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.                                         // 813
 * See the License for the specific language governing permissions and                                              // 814
 * limitations under the License.                                                                                   // 815
 * ========================================================= */                                                     // 816
                                                                                                                    // 817
                                                                                                                    // 818
!function ($) {                                                                                                     // 819
                                                                                                                    // 820
  "use strict"; // jshint ;_;                                                                                       // 821
                                                                                                                    // 822
                                                                                                                    // 823
 /* MODAL CLASS DEFINITION                                                                                          // 824
  * ====================== */                                                                                       // 825
                                                                                                                    // 826
  var Modal = function (element, options) {                                                                         // 827
    this.options = options                                                                                          // 828
    this.$element = $(element)                                                                                      // 829
      .delegate('[data-dismiss="modal"]', 'click.dismiss.modal', $.proxy(this.hide, this))                          // 830
    this.options.remote && this.$element.find('.modal-body').load(this.options.remote)                              // 831
  }                                                                                                                 // 832
                                                                                                                    // 833
  Modal.prototype = {                                                                                               // 834
                                                                                                                    // 835
      constructor: Modal                                                                                            // 836
                                                                                                                    // 837
    , toggle: function () {                                                                                         // 838
        return this[!this.isShown ? 'show' : 'hide']()                                                              // 839
      }                                                                                                             // 840
                                                                                                                    // 841
    , show: function () {                                                                                           // 842
        var that = this                                                                                             // 843
          , e = $.Event('show')                                                                                     // 844
                                                                                                                    // 845
        this.$element.trigger(e)                                                                                    // 846
                                                                                                                    // 847
        if (this.isShown || e.isDefaultPrevented()) return                                                          // 848
                                                                                                                    // 849
        this.isShown = true                                                                                         // 850
                                                                                                                    // 851
        this.escape()                                                                                               // 852
                                                                                                                    // 853
        this.backdrop(function () {                                                                                 // 854
          var transition = $.support.transition && that.$element.hasClass('fade')                                   // 855
                                                                                                                    // 856
          if (!that.$element.parent().length) {                                                                     // 857
            that.$element.appendTo(document.body) //don't move modals dom position                                  // 858
          }                                                                                                         // 859
                                                                                                                    // 860
          that.$element.show()                                                                                      // 861
                                                                                                                    // 862
          if (transition) {                                                                                         // 863
            that.$element[0].offsetWidth // force reflow                                                            // 864
          }                                                                                                         // 865
                                                                                                                    // 866
          that.$element                                                                                             // 867
            .addClass('in')                                                                                         // 868
            .attr('aria-hidden', false)                                                                             // 869
                                                                                                                    // 870
          that.enforceFocus()                                                                                       // 871
                                                                                                                    // 872
          transition ?                                                                                              // 873
            that.$element.one($.support.transition.end, function () { that.$element.focus().trigger('shown') }) :   // 874
            that.$element.focus().trigger('shown')                                                                  // 875
                                                                                                                    // 876
        })                                                                                                          // 877
      }                                                                                                             // 878
                                                                                                                    // 879
    , hide: function (e) {                                                                                          // 880
        e && e.preventDefault()                                                                                     // 881
                                                                                                                    // 882
        var that = this                                                                                             // 883
                                                                                                                    // 884
        e = $.Event('hide')                                                                                         // 885
                                                                                                                    // 886
        this.$element.trigger(e)                                                                                    // 887
                                                                                                                    // 888
        if (!this.isShown || e.isDefaultPrevented()) return                                                         // 889
                                                                                                                    // 890
        this.isShown = false                                                                                        // 891
                                                                                                                    // 892
        this.escape()                                                                                               // 893
                                                                                                                    // 894
        $(document).off('focusin.modal')                                                                            // 895
                                                                                                                    // 896
        this.$element                                                                                               // 897
          .removeClass('in')                                                                                        // 898
          .attr('aria-hidden', true)                                                                                // 899
                                                                                                                    // 900
        $.support.transition && this.$element.hasClass('fade') ?                                                    // 901
          this.hideWithTransition() :                                                                               // 902
          this.hideModal()                                                                                          // 903
      }                                                                                                             // 904
                                                                                                                    // 905
    , enforceFocus: function () {                                                                                   // 906
        var that = this                                                                                             // 907
        $(document).on('focusin.modal', function (e) {                                                              // 908
          if (that.$element[0] !== e.target && !that.$element.has(e.target).length) {                               // 909
            that.$element.focus()                                                                                   // 910
          }                                                                                                         // 911
        })                                                                                                          // 912
      }                                                                                                             // 913
                                                                                                                    // 914
    , escape: function () {                                                                                         // 915
        var that = this                                                                                             // 916
        if (this.isShown && this.options.keyboard) {                                                                // 917
          this.$element.on('keyup.dismiss.modal', function ( e ) {                                                  // 918
            e.which == 27 && that.hide()                                                                            // 919
          })                                                                                                        // 920
        } else if (!this.isShown) {                                                                                 // 921
          this.$element.off('keyup.dismiss.modal')                                                                  // 922
        }                                                                                                           // 923
      }                                                                                                             // 924
                                                                                                                    // 925
    , hideWithTransition: function () {                                                                             // 926
        var that = this                                                                                             // 927
          , timeout = setTimeout(function () {                                                                      // 928
              that.$element.off($.support.transition.end)                                                           // 929
              that.hideModal()                                                                                      // 930
            }, 500)                                                                                                 // 931
                                                                                                                    // 932
        this.$element.one($.support.transition.end, function () {                                                   // 933
          clearTimeout(timeout)                                                                                     // 934
          that.hideModal()                                                                                          // 935
        })                                                                                                          // 936
      }                                                                                                             // 937
                                                                                                                    // 938
    , hideModal: function () {                                                                                      // 939
        var that = this                                                                                             // 940
        this.$element.hide()                                                                                        // 941
        this.backdrop(function () {                                                                                 // 942
          that.removeBackdrop()                                                                                     // 943
          that.$element.trigger('hidden')                                                                           // 944
        })                                                                                                          // 945
      }                                                                                                             // 946
                                                                                                                    // 947
    , removeBackdrop: function () {                                                                                 // 948
        this.$backdrop.remove()                                                                                     // 949
        this.$backdrop = null                                                                                       // 950
      }                                                                                                             // 951
                                                                                                                    // 952
    , backdrop: function (callback) {                                                                               // 953
        var that = this                                                                                             // 954
          , animate = this.$element.hasClass('fade') ? 'fade' : ''                                                  // 955
                                                                                                                    // 956
        if (this.isShown && this.options.backdrop) {                                                                // 957
          var doAnimate = $.support.transition && animate                                                           // 958
                                                                                                                    // 959
          this.$backdrop = $('<div class="modal-backdrop ' + animate + '" />')                                      // 960
            .appendTo(document.body)                                                                                // 961
                                                                                                                    // 962
          this.$backdrop.click(                                                                                     // 963
            this.options.backdrop == 'static' ?                                                                     // 964
              $.proxy(this.$element[0].focus, this.$element[0])                                                     // 965
            : $.proxy(this.hide, this)                                                                              // 966
          )                                                                                                         // 967
                                                                                                                    // 968
          if (doAnimate) this.$backdrop[0].offsetWidth // force reflow                                              // 969
                                                                                                                    // 970
          this.$backdrop.addClass('in')                                                                             // 971
                                                                                                                    // 972
          if (!callback) return                                                                                     // 973
                                                                                                                    // 974
          doAnimate ?                                                                                               // 975
            this.$backdrop.one($.support.transition.end, callback) :                                                // 976
            callback()                                                                                              // 977
                                                                                                                    // 978
        } else if (!this.isShown && this.$backdrop) {                                                               // 979
          this.$backdrop.removeClass('in')                                                                          // 980
                                                                                                                    // 981
          $.support.transition && this.$element.hasClass('fade')?                                                   // 982
            this.$backdrop.one($.support.transition.end, callback) :                                                // 983
            callback()                                                                                              // 984
                                                                                                                    // 985
        } else if (callback) {                                                                                      // 986
          callback()                                                                                                // 987
        }                                                                                                           // 988
      }                                                                                                             // 989
  }                                                                                                                 // 990
                                                                                                                    // 991
                                                                                                                    // 992
 /* MODAL PLUGIN DEFINITION                                                                                         // 993
  * ======================= */                                                                                      // 994
                                                                                                                    // 995
  var old = $.fn.modal                                                                                              // 996
                                                                                                                    // 997
  $.fn.modal = function (option) {                                                                                  // 998
    return this.each(function () {                                                                                  // 999
      var $this = $(this)                                                                                           // 1000
        , data = $this.data('modal')                                                                                // 1001
        , options = $.extend({}, $.fn.modal.defaults, $this.data(), typeof option == 'object' && option)            // 1002
      if (!data) $this.data('modal', (data = new Modal(this, options)))                                             // 1003
      if (typeof option == 'string') data[option]()                                                                 // 1004
      else if (options.show) data.show()                                                                            // 1005
    })                                                                                                              // 1006
  }                                                                                                                 // 1007
                                                                                                                    // 1008
  $.fn.modal.defaults = {                                                                                           // 1009
      backdrop: true                                                                                                // 1010
    , keyboard: true                                                                                                // 1011
    , show: true                                                                                                    // 1012
  }                                                                                                                 // 1013
                                                                                                                    // 1014
  $.fn.modal.Constructor = Modal                                                                                    // 1015
                                                                                                                    // 1016
                                                                                                                    // 1017
 /* MODAL NO CONFLICT                                                                                               // 1018
  * ================= */                                                                                            // 1019
                                                                                                                    // 1020
  $.fn.modal.noConflict = function () {                                                                             // 1021
    $.fn.modal = old                                                                                                // 1022
    return this                                                                                                     // 1023
  }                                                                                                                 // 1024
                                                                                                                    // 1025
                                                                                                                    // 1026
 /* MODAL DATA-API                                                                                                  // 1027
  * ============== */                                                                                               // 1028
                                                                                                                    // 1029
  $(document).on('click.modal.data-api', '[data-toggle="modal"]', function (e) {                                    // 1030
    var $this = $(this)                                                                                             // 1031
      , href = $this.attr('href')                                                                                   // 1032
      , $target = $($this.attr('data-target') || (href && href.replace(/.*(?=#[^\s]+$)/, ''))) //strip for ie7      // 1033
      , option = $target.data('modal') ? 'toggle' : $.extend({ remote:!/#/.test(href) && href }, $target.data(), $this.data())
                                                                                                                    // 1035
    e.preventDefault()                                                                                              // 1036
                                                                                                                    // 1037
    $target                                                                                                         // 1038
      .modal(option)                                                                                                // 1039
      .one('hide', function () {                                                                                    // 1040
        $this.focus()                                                                                               // 1041
      })                                                                                                            // 1042
  })                                                                                                                // 1043
                                                                                                                    // 1044
}(window.jQuery);                                                                                                   // 1045
/* ===========================================================                                                      // 1046
 * bootstrap-tooltip.js v2.3.0                                                                                      // 1047
 * http://twitter.github.com/bootstrap/javascript.html#tooltips                                                     // 1048
 * Inspired by the original jQuery.tipsy by Jason Frame                                                             // 1049
 * ===========================================================                                                      // 1050
 * Copyright 2012 Twitter, Inc.                                                                                     // 1051
 *                                                                                                                  // 1052
 * Licensed under the Apache License, Version 2.0 (the "License");                                                  // 1053
 * you may not use this file except in compliance with the License.                                                 // 1054
 * You may obtain a copy of the License at                                                                          // 1055
 *                                                                                                                  // 1056
 * http://www.apache.org/licenses/LICENSE-2.0                                                                       // 1057
 *                                                                                                                  // 1058
 * Unless required by applicable law or agreed to in writing, software                                              // 1059
 * distributed under the License is distributed on an "AS IS" BASIS,                                                // 1060
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.                                         // 1061
 * See the License for the specific language governing permissions and                                              // 1062
 * limitations under the License.                                                                                   // 1063
 * ========================================================== */                                                    // 1064
                                                                                                                    // 1065
                                                                                                                    // 1066
!function ($) {                                                                                                     // 1067
                                                                                                                    // 1068
  "use strict"; // jshint ;_;                                                                                       // 1069
                                                                                                                    // 1070
                                                                                                                    // 1071
 /* TOOLTIP PUBLIC CLASS DEFINITION                                                                                 // 1072
  * =============================== */                                                                              // 1073
                                                                                                                    // 1074
  var Tooltip = function (element, options) {                                                                       // 1075
    this.init('tooltip', element, options)                                                                          // 1076
  }                                                                                                                 // 1077
                                                                                                                    // 1078
  Tooltip.prototype = {                                                                                             // 1079
                                                                                                                    // 1080
    constructor: Tooltip                                                                                            // 1081
                                                                                                                    // 1082
  , init: function (type, element, options) {                                                                       // 1083
      var eventIn                                                                                                   // 1084
        , eventOut                                                                                                  // 1085
        , triggers                                                                                                  // 1086
        , trigger                                                                                                   // 1087
        , i                                                                                                         // 1088
                                                                                                                    // 1089
      this.type = type                                                                                              // 1090
      this.$element = $(element)                                                                                    // 1091
      this.options = this.getOptions(options)                                                                       // 1092
      this.enabled = true                                                                                           // 1093
                                                                                                                    // 1094
      triggers = this.options.trigger.split(' ')                                                                    // 1095
                                                                                                                    // 1096
      for (i = triggers.length; i--;) {                                                                             // 1097
        trigger = triggers[i]                                                                                       // 1098
        if (trigger == 'click') {                                                                                   // 1099
          this.$element.on('click.' + this.type, this.options.selector, $.proxy(this.toggle, this))                 // 1100
        } else if (trigger != 'manual') {                                                                           // 1101
          eventIn = trigger == 'hover' ? 'mouseenter' : 'focus'                                                     // 1102
          eventOut = trigger == 'hover' ? 'mouseleave' : 'blur'                                                     // 1103
          this.$element.on(eventIn + '.' + this.type, this.options.selector, $.proxy(this.enter, this))             // 1104
          this.$element.on(eventOut + '.' + this.type, this.options.selector, $.proxy(this.leave, this))            // 1105
        }                                                                                                           // 1106
      }                                                                                                             // 1107
                                                                                                                    // 1108
      this.options.selector ?                                                                                       // 1109
        (this._options = $.extend({}, this.options, { trigger: 'manual', selector: '' })) :                         // 1110
        this.fixTitle()                                                                                             // 1111
    }                                                                                                               // 1112
                                                                                                                    // 1113
  , getOptions: function (options) {                                                                                // 1114
      options = $.extend({}, $.fn[this.type].defaults, this.$element.data(), options)                               // 1115
                                                                                                                    // 1116
      if (options.delay && typeof options.delay == 'number') {                                                      // 1117
        options.delay = {                                                                                           // 1118
          show: options.delay                                                                                       // 1119
        , hide: options.delay                                                                                       // 1120
        }                                                                                                           // 1121
      }                                                                                                             // 1122
                                                                                                                    // 1123
      return options                                                                                                // 1124
    }                                                                                                               // 1125
                                                                                                                    // 1126
  , enter: function (e) {                                                                                           // 1127
      var self = $(e.currentTarget)[this.type](this._options).data(this.type)                                       // 1128
                                                                                                                    // 1129
      if (!self.options.delay || !self.options.delay.show) return self.show()                                       // 1130
                                                                                                                    // 1131
      clearTimeout(this.timeout)                                                                                    // 1132
      self.hoverState = 'in'                                                                                        // 1133
      this.timeout = setTimeout(function() {                                                                        // 1134
        if (self.hoverState == 'in') self.show()                                                                    // 1135
      }, self.options.delay.show)                                                                                   // 1136
    }                                                                                                               // 1137
                                                                                                                    // 1138
  , leave: function (e) {                                                                                           // 1139
      var self = $(e.currentTarget)[this.type](this._options).data(this.type)                                       // 1140
                                                                                                                    // 1141
      if (this.timeout) clearTimeout(this.timeout)                                                                  // 1142
      if (!self.options.delay || !self.options.delay.hide) return self.hide()                                       // 1143
                                                                                                                    // 1144
      self.hoverState = 'out'                                                                                       // 1145
      this.timeout = setTimeout(function() {                                                                        // 1146
        if (self.hoverState == 'out') self.hide()                                                                   // 1147
      }, self.options.delay.hide)                                                                                   // 1148
    }                                                                                                               // 1149
                                                                                                                    // 1150
  , show: function () {                                                                                             // 1151
      var $tip                                                                                                      // 1152
        , pos                                                                                                       // 1153
        , actualWidth                                                                                               // 1154
        , actualHeight                                                                                              // 1155
        , placement                                                                                                 // 1156
        , tp                                                                                                        // 1157
        , e = $.Event('show')                                                                                       // 1158
                                                                                                                    // 1159
      if (this.hasContent() && this.enabled) {                                                                      // 1160
        this.$element.trigger(e)                                                                                    // 1161
        if (e.isDefaultPrevented()) return                                                                          // 1162
        $tip = this.tip()                                                                                           // 1163
        this.setContent()                                                                                           // 1164
                                                                                                                    // 1165
        if (this.options.animation) {                                                                               // 1166
          $tip.addClass('fade')                                                                                     // 1167
        }                                                                                                           // 1168
                                                                                                                    // 1169
        placement = typeof this.options.placement == 'function' ?                                                   // 1170
          this.options.placement.call(this, $tip[0], this.$element[0]) :                                            // 1171
          this.options.placement                                                                                    // 1172
                                                                                                                    // 1173
        $tip                                                                                                        // 1174
          .detach()                                                                                                 // 1175
          .css({ top: 0, left: 0, display: 'block' })                                                               // 1176
                                                                                                                    // 1177
        this.options.container ? $tip.appendTo(this.options.container) : $tip.insertAfter(this.$element)            // 1178
                                                                                                                    // 1179
        pos = this.getPosition()                                                                                    // 1180
                                                                                                                    // 1181
        actualWidth = $tip[0].offsetWidth                                                                           // 1182
        actualHeight = $tip[0].offsetHeight                                                                         // 1183
                                                                                                                    // 1184
        switch (placement) {                                                                                        // 1185
          case 'bottom':                                                                                            // 1186
            tp = {top: pos.top + pos.height, left: pos.left + pos.width / 2 - actualWidth / 2}                      // 1187
            break                                                                                                   // 1188
          case 'top':                                                                                               // 1189
            tp = {top: pos.top - actualHeight, left: pos.left + pos.width / 2 - actualWidth / 2}                    // 1190
            break                                                                                                   // 1191
          case 'left':                                                                                              // 1192
            tp = {top: pos.top + pos.height / 2 - actualHeight / 2, left: pos.left - actualWidth}                   // 1193
            break                                                                                                   // 1194
          case 'right':                                                                                             // 1195
            tp = {top: pos.top + pos.height / 2 - actualHeight / 2, left: pos.left + pos.width}                     // 1196
            break                                                                                                   // 1197
        }                                                                                                           // 1198
                                                                                                                    // 1199
        this.applyPlacement(tp, placement)                                                                          // 1200
        this.$element.trigger('shown')                                                                              // 1201
      }                                                                                                             // 1202
    }                                                                                                               // 1203
                                                                                                                    // 1204
  , applyPlacement: function(offset, placement){                                                                    // 1205
      var $tip = this.tip()                                                                                         // 1206
        , width = $tip[0].offsetWidth                                                                               // 1207
        , height = $tip[0].offsetHeight                                                                             // 1208
        , actualWidth                                                                                               // 1209
        , actualHeight                                                                                              // 1210
        , delta                                                                                                     // 1211
        , replace                                                                                                   // 1212
                                                                                                                    // 1213
      $tip                                                                                                          // 1214
        .offset(offset)                                                                                             // 1215
        .addClass(placement)                                                                                        // 1216
        .addClass('in')                                                                                             // 1217
                                                                                                                    // 1218
      actualWidth = $tip[0].offsetWidth                                                                             // 1219
      actualHeight = $tip[0].offsetHeight                                                                           // 1220
                                                                                                                    // 1221
      if (placement == 'top' && actualHeight != height) {                                                           // 1222
        offset.top = offset.top + height - actualHeight                                                             // 1223
        replace = true                                                                                              // 1224
      }                                                                                                             // 1225
                                                                                                                    // 1226
      if (placement == 'bottom' || placement == 'top') {                                                            // 1227
        delta = 0                                                                                                   // 1228
                                                                                                                    // 1229
        if (offset.left < 0){                                                                                       // 1230
          delta = offset.left * -2                                                                                  // 1231
          offset.left = 0                                                                                           // 1232
          $tip.offset(offset)                                                                                       // 1233
          actualWidth = $tip[0].offsetWidth                                                                         // 1234
          actualHeight = $tip[0].offsetHeight                                                                       // 1235
        }                                                                                                           // 1236
                                                                                                                    // 1237
        this.replaceArrow(delta - width + actualWidth, actualWidth, 'left')                                         // 1238
      } else {                                                                                                      // 1239
        this.replaceArrow(actualHeight - height, actualHeight, 'top')                                               // 1240
      }                                                                                                             // 1241
                                                                                                                    // 1242
      if (replace) $tip.offset(offset)                                                                              // 1243
    }                                                                                                               // 1244
                                                                                                                    // 1245
  , replaceArrow: function(delta, dimension, position){                                                             // 1246
      this                                                                                                          // 1247
        .arrow()                                                                                                    // 1248
        .css(position, delta ? (50 * (1 - delta / dimension) + "%") : '')                                           // 1249
    }                                                                                                               // 1250
                                                                                                                    // 1251
  , setContent: function () {                                                                                       // 1252
      var $tip = this.tip()                                                                                         // 1253
        , title = this.getTitle()                                                                                   // 1254
                                                                                                                    // 1255
      $tip.find('.tooltip-inner')[this.options.html ? 'html' : 'text'](title)                                       // 1256
      $tip.removeClass('fade in top bottom left right')                                                             // 1257
    }                                                                                                               // 1258
                                                                                                                    // 1259
  , hide: function () {                                                                                             // 1260
      var that = this                                                                                               // 1261
        , $tip = this.tip()                                                                                         // 1262
        , e = $.Event('hide')                                                                                       // 1263
                                                                                                                    // 1264
      this.$element.trigger(e)                                                                                      // 1265
      if (e.isDefaultPrevented()) return                                                                            // 1266
                                                                                                                    // 1267
      $tip.removeClass('in')                                                                                        // 1268
                                                                                                                    // 1269
      function removeWithAnimation() {                                                                              // 1270
        var timeout = setTimeout(function () {                                                                      // 1271
          $tip.off($.support.transition.end).detach()                                                               // 1272
        }, 500)                                                                                                     // 1273
                                                                                                                    // 1274
        $tip.one($.support.transition.end, function () {                                                            // 1275
          clearTimeout(timeout)                                                                                     // 1276
          $tip.detach()                                                                                             // 1277
        })                                                                                                          // 1278
      }                                                                                                             // 1279
                                                                                                                    // 1280
      $.support.transition && this.$tip.hasClass('fade') ?                                                          // 1281
        removeWithAnimation() :                                                                                     // 1282
        $tip.detach()                                                                                               // 1283
                                                                                                                    // 1284
      this.$element.trigger('hidden')                                                                               // 1285
                                                                                                                    // 1286
      return this                                                                                                   // 1287
    }                                                                                                               // 1288
                                                                                                                    // 1289
  , fixTitle: function () {                                                                                         // 1290
      var $e = this.$element                                                                                        // 1291
      if ($e.attr('title') || typeof($e.attr('data-original-title')) != 'string') {                                 // 1292
        $e.attr('data-original-title', $e.attr('title') || '').attr('title', '')                                    // 1293
      }                                                                                                             // 1294
    }                                                                                                               // 1295
                                                                                                                    // 1296
  , hasContent: function () {                                                                                       // 1297
      return this.getTitle()                                                                                        // 1298
    }                                                                                                               // 1299
                                                                                                                    // 1300
  , getPosition: function () {                                                                                      // 1301
      var el = this.$element[0]                                                                                     // 1302
      return $.extend({}, (typeof el.getBoundingClientRect == 'function') ? el.getBoundingClientRect() : {          // 1303
        width: el.offsetWidth                                                                                       // 1304
      , height: el.offsetHeight                                                                                     // 1305
      }, this.$element.offset())                                                                                    // 1306
    }                                                                                                               // 1307
                                                                                                                    // 1308
  , getTitle: function () {                                                                                         // 1309
      var title                                                                                                     // 1310
        , $e = this.$element                                                                                        // 1311
        , o = this.options                                                                                          // 1312
                                                                                                                    // 1313
      title = $e.attr('data-original-title')                                                                        // 1314
        || (typeof o.title == 'function' ? o.title.call($e[0]) :  o.title)                                          // 1315
                                                                                                                    // 1316
      return title                                                                                                  // 1317
    }                                                                                                               // 1318
                                                                                                                    // 1319
  , tip: function () {                                                                                              // 1320
      return this.$tip = this.$tip || $(this.options.template)                                                      // 1321
    }                                                                                                               // 1322
                                                                                                                    // 1323
  , arrow: function(){                                                                                              // 1324
      return this.$arrow = this.$arrow || this.tip().find(".tooltip-arrow")                                         // 1325
    }                                                                                                               // 1326
                                                                                                                    // 1327
  , validate: function () {                                                                                         // 1328
      if (!this.$element[0].parentNode) {                                                                           // 1329
        this.hide()                                                                                                 // 1330
        this.$element = null                                                                                        // 1331
        this.options = null                                                                                         // 1332
      }                                                                                                             // 1333
    }                                                                                                               // 1334
                                                                                                                    // 1335
  , enable: function () {                                                                                           // 1336
      this.enabled = true                                                                                           // 1337
    }                                                                                                               // 1338
                                                                                                                    // 1339
  , disable: function () {                                                                                          // 1340
      this.enabled = false                                                                                          // 1341
    }                                                                                                               // 1342
                                                                                                                    // 1343
  , toggleEnabled: function () {                                                                                    // 1344
      this.enabled = !this.enabled                                                                                  // 1345
    }                                                                                                               // 1346
                                                                                                                    // 1347
  , toggle: function (e) {                                                                                          // 1348
      var self = e ? $(e.currentTarget)[this.type](this._options).data(this.type) : this                            // 1349
      self.tip().hasClass('in') ? self.hide() : self.show()                                                         // 1350
    }                                                                                                               // 1351
                                                                                                                    // 1352
  , destroy: function () {                                                                                          // 1353
      this.hide().$element.off('.' + this.type).removeData(this.type)                                               // 1354
    }                                                                                                               // 1355
                                                                                                                    // 1356
  }                                                                                                                 // 1357
                                                                                                                    // 1358
                                                                                                                    // 1359
 /* TOOLTIP PLUGIN DEFINITION                                                                                       // 1360
  * ========================= */                                                                                    // 1361
                                                                                                                    // 1362
  var old = $.fn.tooltip                                                                                            // 1363
                                                                                                                    // 1364
  $.fn.tooltip = function ( option ) {                                                                              // 1365
    return this.each(function () {                                                                                  // 1366
      var $this = $(this)                                                                                           // 1367
        , data = $this.data('tooltip')                                                                              // 1368
        , options = typeof option == 'object' && option                                                             // 1369
      if (!data) $this.data('tooltip', (data = new Tooltip(this, options)))                                         // 1370
      if (typeof option == 'string') data[option]()                                                                 // 1371
    })                                                                                                              // 1372
  }                                                                                                                 // 1373
                                                                                                                    // 1374
  $.fn.tooltip.Constructor = Tooltip                                                                                // 1375
                                                                                                                    // 1376
  $.fn.tooltip.defaults = {                                                                                         // 1377
    animation: true                                                                                                 // 1378
  , placement: 'top'                                                                                                // 1379
  , selector: false                                                                                                 // 1380
  , template: '<div class="tooltip"><div class="tooltip-arrow"></div><div class="tooltip-inner"></div></div>'       // 1381
  , trigger: 'hover focus'                                                                                          // 1382
  , title: ''                                                                                                       // 1383
  , delay: 0                                                                                                        // 1384
  , html: false                                                                                                     // 1385
  , container: false                                                                                                // 1386
  }                                                                                                                 // 1387
                                                                                                                    // 1388
                                                                                                                    // 1389
 /* TOOLTIP NO CONFLICT                                                                                             // 1390
  * =================== */                                                                                          // 1391
                                                                                                                    // 1392
  $.fn.tooltip.noConflict = function () {                                                                           // 1393
    $.fn.tooltip = old                                                                                              // 1394
    return this                                                                                                     // 1395
  }                                                                                                                 // 1396
                                                                                                                    // 1397
}(window.jQuery);                                                                                                   // 1398
/* ===========================================================                                                      // 1399
 * bootstrap-popover.js v2.3.0                                                                                      // 1400
 * http://twitter.github.com/bootstrap/javascript.html#popovers                                                     // 1401
 * ===========================================================                                                      // 1402
 * Copyright 2012 Twitter, Inc.                                                                                     // 1403
 *                                                                                                                  // 1404
 * Licensed under the Apache License, Version 2.0 (the "License");                                                  // 1405
 * you may not use this file except in compliance with the License.                                                 // 1406
 * You may obtain a copy of the License at                                                                          // 1407
 *                                                                                                                  // 1408
 * http://www.apache.org/licenses/LICENSE-2.0                                                                       // 1409
 *                                                                                                                  // 1410
 * Unless required by applicable law or agreed to in writing, software                                              // 1411
 * distributed under the License is distributed on an "AS IS" BASIS,                                                // 1412
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.                                         // 1413
 * See the License for the specific language governing permissions and                                              // 1414
 * limitations under the License.                                                                                   // 1415
 * =========================================================== */                                                   // 1416
                                                                                                                    // 1417
                                                                                                                    // 1418
!function ($) {                                                                                                     // 1419
                                                                                                                    // 1420
  "use strict"; // jshint ;_;                                                                                       // 1421
                                                                                                                    // 1422
                                                                                                                    // 1423
 /* POPOVER PUBLIC CLASS DEFINITION                                                                                 // 1424
  * =============================== */                                                                              // 1425
                                                                                                                    // 1426
  var Popover = function (element, options) {                                                                       // 1427
    this.init('popover', element, options)                                                                          // 1428
  }                                                                                                                 // 1429
                                                                                                                    // 1430
                                                                                                                    // 1431
  /* NOTE: POPOVER EXTENDS BOOTSTRAP-TOOLTIP.js                                                                     // 1432
     ========================================== */                                                                  // 1433
                                                                                                                    // 1434
  Popover.prototype = $.extend({}, $.fn.tooltip.Constructor.prototype, {                                            // 1435
                                                                                                                    // 1436
    constructor: Popover                                                                                            // 1437
                                                                                                                    // 1438
  , setContent: function () {                                                                                       // 1439
      var $tip = this.tip()                                                                                         // 1440
        , title = this.getTitle()                                                                                   // 1441
        , content = this.getContent()                                                                               // 1442
                                                                                                                    // 1443
      $tip.find('.popover-title')[this.options.html ? 'html' : 'text'](title)                                       // 1444
      $tip.find('.popover-content')[this.options.html ? 'html' : 'text'](content)                                   // 1445
                                                                                                                    // 1446
      $tip.removeClass('fade top bottom left right in')                                                             // 1447
    }                                                                                                               // 1448
                                                                                                                    // 1449
  , hasContent: function () {                                                                                       // 1450
      return this.getTitle() || this.getContent()                                                                   // 1451
    }                                                                                                               // 1452
                                                                                                                    // 1453
  , getContent: function () {                                                                                       // 1454
      var content                                                                                                   // 1455
        , $e = this.$element                                                                                        // 1456
        , o = this.options                                                                                          // 1457
                                                                                                                    // 1458
      content = (typeof o.content == 'function' ? o.content.call($e[0]) :  o.content)                               // 1459
        || $e.attr('data-content')                                                                                  // 1460
                                                                                                                    // 1461
      return content                                                                                                // 1462
    }                                                                                                               // 1463
                                                                                                                    // 1464
  , tip: function () {                                                                                              // 1465
      if (!this.$tip) {                                                                                             // 1466
        this.$tip = $(this.options.template)                                                                        // 1467
      }                                                                                                             // 1468
      return this.$tip                                                                                              // 1469
    }                                                                                                               // 1470
                                                                                                                    // 1471
  , destroy: function () {                                                                                          // 1472
      this.hide().$element.off('.' + this.type).removeData(this.type)                                               // 1473
    }                                                                                                               // 1474
                                                                                                                    // 1475
  })                                                                                                                // 1476
                                                                                                                    // 1477
                                                                                                                    // 1478
 /* POPOVER PLUGIN DEFINITION                                                                                       // 1479
  * ======================= */                                                                                      // 1480
                                                                                                                    // 1481
  var old = $.fn.popover                                                                                            // 1482
                                                                                                                    // 1483
  $.fn.popover = function (option) {                                                                                // 1484
    return this.each(function () {                                                                                  // 1485
      var $this = $(this)                                                                                           // 1486
        , data = $this.data('popover')                                                                              // 1487
        , options = typeof option == 'object' && option                                                             // 1488
      if (!data) $this.data('popover', (data = new Popover(this, options)))                                         // 1489
      if (typeof option == 'string') data[option]()                                                                 // 1490
    })                                                                                                              // 1491
  }                                                                                                                 // 1492
                                                                                                                    // 1493
  $.fn.popover.Constructor = Popover                                                                                // 1494
                                                                                                                    // 1495
  $.fn.popover.defaults = $.extend({} , $.fn.tooltip.defaults, {                                                    // 1496
    placement: 'right'                                                                                              // 1497
  , trigger: 'click'                                                                                                // 1498
  , content: ''                                                                                                     // 1499
  , template: '<div class="popover"><div class="arrow"></div><h3 class="popover-title"></h3><div class="popover-content"></div></div>'
  })                                                                                                                // 1501
                                                                                                                    // 1502
                                                                                                                    // 1503
 /* POPOVER NO CONFLICT                                                                                             // 1504
  * =================== */                                                                                          // 1505
                                                                                                                    // 1506
  $.fn.popover.noConflict = function () {                                                                           // 1507
    $.fn.popover = old                                                                                              // 1508
    return this                                                                                                     // 1509
  }                                                                                                                 // 1510
                                                                                                                    // 1511
}(window.jQuery);                                                                                                   // 1512
/* =============================================================                                                    // 1513
 * bootstrap-scrollspy.js v2.3.0                                                                                    // 1514
 * http://twitter.github.com/bootstrap/javascript.html#scrollspy                                                    // 1515
 * =============================================================                                                    // 1516
 * Copyright 2012 Twitter, Inc.                                                                                     // 1517
 *                                                                                                                  // 1518
 * Licensed under the Apache License, Version 2.0 (the "License");                                                  // 1519
 * you may not use this file except in compliance with the License.                                                 // 1520
 * You may obtain a copy of the License at                                                                          // 1521
 *                                                                                                                  // 1522
 * http://www.apache.org/licenses/LICENSE-2.0                                                                       // 1523
 *                                                                                                                  // 1524
 * Unless required by applicable law or agreed to in writing, software                                              // 1525
 * distributed under the License is distributed on an "AS IS" BASIS,                                                // 1526
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.                                         // 1527
 * See the License for the specific language governing permissions and                                              // 1528
 * limitations under the License.                                                                                   // 1529
 * ============================================================== */                                                // 1530
                                                                                                                    // 1531
                                                                                                                    // 1532
!function ($) {                                                                                                     // 1533
                                                                                                                    // 1534
  "use strict"; // jshint ;_;                                                                                       // 1535
                                                                                                                    // 1536
                                                                                                                    // 1537
 /* SCROLLSPY CLASS DEFINITION                                                                                      // 1538
  * ========================== */                                                                                   // 1539
                                                                                                                    // 1540
  function ScrollSpy(element, options) {                                                                            // 1541
    var process = $.proxy(this.process, this)                                                                       // 1542
      , $element = $(element).is('body') ? $(window) : $(element)                                                   // 1543
      , href                                                                                                        // 1544
    this.options = $.extend({}, $.fn.scrollspy.defaults, options)                                                   // 1545
    this.$scrollElement = $element.on('scroll.scroll-spy.data-api', process)                                        // 1546
    this.selector = (this.options.target                                                                            // 1547
      || ((href = $(element).attr('href')) && href.replace(/.*(?=#[^\s]+$)/, '')) //strip for ie7                   // 1548
      || '') + ' .nav li > a'                                                                                       // 1549
    this.$body = $('body')                                                                                          // 1550
    this.refresh()                                                                                                  // 1551
    this.process()                                                                                                  // 1552
  }                                                                                                                 // 1553
                                                                                                                    // 1554
  ScrollSpy.prototype = {                                                                                           // 1555
                                                                                                                    // 1556
      constructor: ScrollSpy                                                                                        // 1557
                                                                                                                    // 1558
    , refresh: function () {                                                                                        // 1559
        var self = this                                                                                             // 1560
          , $targets                                                                                                // 1561
                                                                                                                    // 1562
        this.offsets = $([])                                                                                        // 1563
        this.targets = $([])                                                                                        // 1564
                                                                                                                    // 1565
        $targets = this.$body                                                                                       // 1566
          .find(this.selector)                                                                                      // 1567
          .map(function () {                                                                                        // 1568
            var $el = $(this)                                                                                       // 1569
              , href = $el.data('target') || $el.attr('href')                                                       // 1570
              , $href = /^#\w/.test(href) && $(href)                                                                // 1571
            return ( $href                                                                                          // 1572
              && $href.length                                                                                       // 1573
              && [[ $href.position().top + (!$.isWindow(self.$scrollElement.get(0)) && self.$scrollElement.scrollTop()), href ]] ) || null
          })                                                                                                        // 1575
          .sort(function (a, b) { return a[0] - b[0] })                                                             // 1576
          .each(function () {                                                                                       // 1577
            self.offsets.push(this[0])                                                                              // 1578
            self.targets.push(this[1])                                                                              // 1579
          })                                                                                                        // 1580
      }                                                                                                             // 1581
                                                                                                                    // 1582
    , process: function () {                                                                                        // 1583
        var scrollTop = this.$scrollElement.scrollTop() + this.options.offset                                       // 1584
          , scrollHeight = this.$scrollElement[0].scrollHeight || this.$body[0].scrollHeight                        // 1585
          , maxScroll = scrollHeight - this.$scrollElement.height()                                                 // 1586
          , offsets = this.offsets                                                                                  // 1587
          , targets = this.targets                                                                                  // 1588
          , activeTarget = this.activeTarget                                                                        // 1589
          , i                                                                                                       // 1590
                                                                                                                    // 1591
        if (scrollTop >= maxScroll) {                                                                               // 1592
          return activeTarget != (i = targets.last()[0])                                                            // 1593
            && this.activate ( i )                                                                                  // 1594
        }                                                                                                           // 1595
                                                                                                                    // 1596
        for (i = offsets.length; i--;) {                                                                            // 1597
          activeTarget != targets[i]                                                                                // 1598
            && scrollTop >= offsets[i]                                                                              // 1599
            && (!offsets[i + 1] || scrollTop <= offsets[i + 1])                                                     // 1600
            && this.activate( targets[i] )                                                                          // 1601
        }                                                                                                           // 1602
      }                                                                                                             // 1603
                                                                                                                    // 1604
    , activate: function (target) {                                                                                 // 1605
        var active                                                                                                  // 1606
          , selector                                                                                                // 1607
                                                                                                                    // 1608
        this.activeTarget = target                                                                                  // 1609
                                                                                                                    // 1610
        $(this.selector)                                                                                            // 1611
          .parent('.active')                                                                                        // 1612
          .removeClass('active')                                                                                    // 1613
                                                                                                                    // 1614
        selector = this.selector                                                                                    // 1615
          + '[data-target="' + target + '"],'                                                                       // 1616
          + this.selector + '[href="' + target + '"]'                                                               // 1617
                                                                                                                    // 1618
        active = $(selector)                                                                                        // 1619
          .parent('li')                                                                                             // 1620
          .addClass('active')                                                                                       // 1621
                                                                                                                    // 1622
        if (active.parent('.dropdown-menu').length)  {                                                              // 1623
          active = active.closest('li.dropdown').addClass('active')                                                 // 1624
        }                                                                                                           // 1625
                                                                                                                    // 1626
        active.trigger('activate')                                                                                  // 1627
      }                                                                                                             // 1628
                                                                                                                    // 1629
  }                                                                                                                 // 1630
                                                                                                                    // 1631
                                                                                                                    // 1632
 /* SCROLLSPY PLUGIN DEFINITION                                                                                     // 1633
  * =========================== */                                                                                  // 1634
                                                                                                                    // 1635
  var old = $.fn.scrollspy                                                                                          // 1636
                                                                                                                    // 1637
  $.fn.scrollspy = function (option) {                                                                              // 1638
    return this.each(function () {                                                                                  // 1639
      var $this = $(this)                                                                                           // 1640
        , data = $this.data('scrollspy')                                                                            // 1641
        , options = typeof option == 'object' && option                                                             // 1642
      if (!data) $this.data('scrollspy', (data = new ScrollSpy(this, options)))                                     // 1643
      if (typeof option == 'string') data[option]()                                                                 // 1644
    })                                                                                                              // 1645
  }                                                                                                                 // 1646
                                                                                                                    // 1647
  $.fn.scrollspy.Constructor = ScrollSpy                                                                            // 1648
                                                                                                                    // 1649
  $.fn.scrollspy.defaults = {                                                                                       // 1650
    offset: 10                                                                                                      // 1651
  }                                                                                                                 // 1652
                                                                                                                    // 1653
                                                                                                                    // 1654
 /* SCROLLSPY NO CONFLICT                                                                                           // 1655
  * ===================== */                                                                                        // 1656
                                                                                                                    // 1657
  $.fn.scrollspy.noConflict = function () {                                                                         // 1658
    $.fn.scrollspy = old                                                                                            // 1659
    return this                                                                                                     // 1660
  }                                                                                                                 // 1661
                                                                                                                    // 1662
                                                                                                                    // 1663
 /* SCROLLSPY DATA-API                                                                                              // 1664
  * ================== */                                                                                           // 1665
                                                                                                                    // 1666
  $(window).on('load', function () {                                                                                // 1667
    $('[data-spy="scroll"]').each(function () {                                                                     // 1668
      var $spy = $(this)                                                                                            // 1669
      $spy.scrollspy($spy.data())                                                                                   // 1670
    })                                                                                                              // 1671
  })                                                                                                                // 1672
                                                                                                                    // 1673
}(window.jQuery);/* ========================================================                                        // 1674
 * bootstrap-tab.js v2.3.0                                                                                          // 1675
 * http://twitter.github.com/bootstrap/javascript.html#tabs                                                         // 1676
 * ========================================================                                                         // 1677
 * Copyright 2012 Twitter, Inc.                                                                                     // 1678
 *                                                                                                                  // 1679
 * Licensed under the Apache License, Version 2.0 (the "License");                                                  // 1680
 * you may not use this file except in compliance with the License.                                                 // 1681
 * You may obtain a copy of the License at                                                                          // 1682
 *                                                                                                                  // 1683
 * http://www.apache.org/licenses/LICENSE-2.0                                                                       // 1684
 *                                                                                                                  // 1685
 * Unless required by applicable law or agreed to in writing, software                                              // 1686
 * distributed under the License is distributed on an "AS IS" BASIS,                                                // 1687
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.                                         // 1688
 * See the License for the specific language governing permissions and                                              // 1689
 * limitations under the License.                                                                                   // 1690
 * ======================================================== */                                                      // 1691
                                                                                                                    // 1692
                                                                                                                    // 1693
!function ($) {                                                                                                     // 1694
                                                                                                                    // 1695
  "use strict"; // jshint ;_;                                                                                       // 1696
                                                                                                                    // 1697
                                                                                                                    // 1698
 /* TAB CLASS DEFINITION                                                                                            // 1699
  * ==================== */                                                                                         // 1700
                                                                                                                    // 1701
  var Tab = function (element) {                                                                                    // 1702
    this.element = $(element)                                                                                       // 1703
  }                                                                                                                 // 1704
                                                                                                                    // 1705
  Tab.prototype = {                                                                                                 // 1706
                                                                                                                    // 1707
    constructor: Tab                                                                                                // 1708
                                                                                                                    // 1709
  , show: function () {                                                                                             // 1710
      var $this = this.element                                                                                      // 1711
        , $ul = $this.closest('ul:not(.dropdown-menu)')                                                             // 1712
        , selector = $this.attr('data-target')                                                                      // 1713
        , previous                                                                                                  // 1714
        , $target                                                                                                   // 1715
        , e                                                                                                         // 1716
                                                                                                                    // 1717
      if (!selector) {                                                                                              // 1718
        selector = $this.attr('href')                                                                               // 1719
        selector = selector && selector.replace(/.*(?=#[^\s]*$)/, '') //strip for ie7                               // 1720
      }                                                                                                             // 1721
                                                                                                                    // 1722
      if ( $this.parent('li').hasClass('active') ) return                                                           // 1723
                                                                                                                    // 1724
      previous = $ul.find('.active:last a')[0]                                                                      // 1725
                                                                                                                    // 1726
      e = $.Event('show', {                                                                                         // 1727
        relatedTarget: previous                                                                                     // 1728
      })                                                                                                            // 1729
                                                                                                                    // 1730
      $this.trigger(e)                                                                                              // 1731
                                                                                                                    // 1732
      if (e.isDefaultPrevented()) return                                                                            // 1733
                                                                                                                    // 1734
      $target = $(selector)                                                                                         // 1735
                                                                                                                    // 1736
      this.activate($this.parent('li'), $ul)                                                                        // 1737
      this.activate($target, $target.parent(), function () {                                                        // 1738
        $this.trigger({                                                                                             // 1739
          type: 'shown'                                                                                             // 1740
        , relatedTarget: previous                                                                                   // 1741
        })                                                                                                          // 1742
      })                                                                                                            // 1743
    }                                                                                                               // 1744
                                                                                                                    // 1745
  , activate: function ( element, container, callback) {                                                            // 1746
      var $active = container.find('> .active')                                                                     // 1747
        , transition = callback                                                                                     // 1748
            && $.support.transition                                                                                 // 1749
            && $active.hasClass('fade')                                                                             // 1750
                                                                                                                    // 1751
      function next() {                                                                                             // 1752
        $active                                                                                                     // 1753
          .removeClass('active')                                                                                    // 1754
          .find('> .dropdown-menu > .active')                                                                       // 1755
          .removeClass('active')                                                                                    // 1756
                                                                                                                    // 1757
        element.addClass('active')                                                                                  // 1758
                                                                                                                    // 1759
        if (transition) {                                                                                           // 1760
          element[0].offsetWidth // reflow for transition                                                           // 1761
          element.addClass('in')                                                                                    // 1762
        } else {                                                                                                    // 1763
          element.removeClass('fade')                                                                               // 1764
        }                                                                                                           // 1765
                                                                                                                    // 1766
        if ( element.parent('.dropdown-menu') ) {                                                                   // 1767
          element.closest('li.dropdown').addClass('active')                                                         // 1768
        }                                                                                                           // 1769
                                                                                                                    // 1770
        callback && callback()                                                                                      // 1771
      }                                                                                                             // 1772
                                                                                                                    // 1773
      transition ?                                                                                                  // 1774
        $active.one($.support.transition.end, next) :                                                               // 1775
        next()                                                                                                      // 1776
                                                                                                                    // 1777
      $active.removeClass('in')                                                                                     // 1778
    }                                                                                                               // 1779
  }                                                                                                                 // 1780
                                                                                                                    // 1781
                                                                                                                    // 1782
 /* TAB PLUGIN DEFINITION                                                                                           // 1783
  * ===================== */                                                                                        // 1784
                                                                                                                    // 1785
  var old = $.fn.tab                                                                                                // 1786
                                                                                                                    // 1787
  $.fn.tab = function ( option ) {                                                                                  // 1788
    return this.each(function () {                                                                                  // 1789
      var $this = $(this)                                                                                           // 1790
        , data = $this.data('tab')                                                                                  // 1791
      if (!data) $this.data('tab', (data = new Tab(this)))                                                          // 1792
      if (typeof option == 'string') data[option]()                                                                 // 1793
    })                                                                                                              // 1794
  }                                                                                                                 // 1795
                                                                                                                    // 1796
  $.fn.tab.Constructor = Tab                                                                                        // 1797
                                                                                                                    // 1798
                                                                                                                    // 1799
 /* TAB NO CONFLICT                                                                                                 // 1800
  * =============== */                                                                                              // 1801
                                                                                                                    // 1802
  $.fn.tab.noConflict = function () {                                                                               // 1803
    $.fn.tab = old                                                                                                  // 1804
    return this                                                                                                     // 1805
  }                                                                                                                 // 1806
                                                                                                                    // 1807
                                                                                                                    // 1808
 /* TAB DATA-API                                                                                                    // 1809
  * ============ */                                                                                                 // 1810
                                                                                                                    // 1811
  $(document).on('click.tab.data-api', '[data-toggle="tab"], [data-toggle="pill"]', function (e) {                  // 1812
    e.preventDefault()                                                                                              // 1813
    $(this).tab('show')                                                                                             // 1814
  })                                                                                                                // 1815
                                                                                                                    // 1816
}(window.jQuery);/* =============================================================                                   // 1817
 * bootstrap-typeahead.js v2.3.0                                                                                    // 1818
 * http://twitter.github.com/bootstrap/javascript.html#typeahead                                                    // 1819
 * =============================================================                                                    // 1820
 * Copyright 2012 Twitter, Inc.                                                                                     // 1821
 *                                                                                                                  // 1822
 * Licensed under the Apache License, Version 2.0 (the "License");                                                  // 1823
 * you may not use this file except in compliance with the License.                                                 // 1824
 * You may obtain a copy of the License at                                                                          // 1825
 *                                                                                                                  // 1826
 * http://www.apache.org/licenses/LICENSE-2.0                                                                       // 1827
 *                                                                                                                  // 1828
 * Unless required by applicable law or agreed to in writing, software                                              // 1829
 * distributed under the License is distributed on an "AS IS" BASIS,                                                // 1830
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.                                         // 1831
 * See the License for the specific language governing permissions and                                              // 1832
 * limitations under the License.                                                                                   // 1833
 * ============================================================ */                                                  // 1834
                                                                                                                    // 1835
                                                                                                                    // 1836
!function($){                                                                                                       // 1837
                                                                                                                    // 1838
  "use strict"; // jshint ;_;                                                                                       // 1839
                                                                                                                    // 1840
                                                                                                                    // 1841
 /* TYPEAHEAD PUBLIC CLASS DEFINITION                                                                               // 1842
  * ================================= */                                                                            // 1843
                                                                                                                    // 1844
  var Typeahead = function (element, options) {                                                                     // 1845
    this.$element = $(element)                                                                                      // 1846
    this.options = $.extend({}, $.fn.typeahead.defaults, options)                                                   // 1847
    this.matcher = this.options.matcher || this.matcher                                                             // 1848
    this.sorter = this.options.sorter || this.sorter                                                                // 1849
    this.highlighter = this.options.highlighter || this.highlighter                                                 // 1850
    this.updater = this.options.updater || this.updater                                                             // 1851
    this.source = this.options.source                                                                               // 1852
    this.$menu = $(this.options.menu)                                                                               // 1853
    this.shown = false                                                                                              // 1854
    this.listen()                                                                                                   // 1855
  }                                                                                                                 // 1856
                                                                                                                    // 1857
  Typeahead.prototype = {                                                                                           // 1858
                                                                                                                    // 1859
    constructor: Typeahead                                                                                          // 1860
                                                                                                                    // 1861
  , select: function () {                                                                                           // 1862
      var val = this.$menu.find('.active').attr('data-value')                                                       // 1863
      this.$element                                                                                                 // 1864
        .val(this.updater(val))                                                                                     // 1865
        .change()                                                                                                   // 1866
      return this.hide()                                                                                            // 1867
    }                                                                                                               // 1868
                                                                                                                    // 1869
  , updater: function (item) {                                                                                      // 1870
      return item                                                                                                   // 1871
    }                                                                                                               // 1872
                                                                                                                    // 1873
  , show: function () {                                                                                             // 1874
      var pos = $.extend({}, this.$element.position(), {                                                            // 1875
        height: this.$element[0].offsetHeight                                                                       // 1876
      })                                                                                                            // 1877
                                                                                                                    // 1878
      this.$menu                                                                                                    // 1879
        .insertAfter(this.$element)                                                                                 // 1880
        .css({                                                                                                      // 1881
          top: pos.top + pos.height                                                                                 // 1882
        , left: pos.left                                                                                            // 1883
        })                                                                                                          // 1884
        .show()                                                                                                     // 1885
                                                                                                                    // 1886
      this.shown = true                                                                                             // 1887
      return this                                                                                                   // 1888
    }                                                                                                               // 1889
                                                                                                                    // 1890
  , hide: function () {                                                                                             // 1891
      this.$menu.hide()                                                                                             // 1892
      this.shown = false                                                                                            // 1893
      return this                                                                                                   // 1894
    }                                                                                                               // 1895
                                                                                                                    // 1896
  , lookup: function (event) {                                                                                      // 1897
      var items                                                                                                     // 1898
                                                                                                                    // 1899
      this.query = this.$element.val()                                                                              // 1900
                                                                                                                    // 1901
      if (!this.query || this.query.length < this.options.minLength) {                                              // 1902
        return this.shown ? this.hide() : this                                                                      // 1903
      }                                                                                                             // 1904
                                                                                                                    // 1905
      items = $.isFunction(this.source) ? this.source(this.query, $.proxy(this.process, this)) : this.source        // 1906
                                                                                                                    // 1907
      return items ? this.process(items) : this                                                                     // 1908
    }                                                                                                               // 1909
                                                                                                                    // 1910
  , process: function (items) {                                                                                     // 1911
      var that = this                                                                                               // 1912
                                                                                                                    // 1913
      items = $.grep(items, function (item) {                                                                       // 1914
        return that.matcher(item)                                                                                   // 1915
      })                                                                                                            // 1916
                                                                                                                    // 1917
      items = this.sorter(items)                                                                                    // 1918
                                                                                                                    // 1919
      if (!items.length) {                                                                                          // 1920
        return this.shown ? this.hide() : this                                                                      // 1921
      }                                                                                                             // 1922
                                                                                                                    // 1923
      return this.render(items.slice(0, this.options.items)).show()                                                 // 1924
    }                                                                                                               // 1925
                                                                                                                    // 1926
  , matcher: function (item) {                                                                                      // 1927
      return ~item.toLowerCase().indexOf(this.query.toLowerCase())                                                  // 1928
    }                                                                                                               // 1929
                                                                                                                    // 1930
  , sorter: function (items) {                                                                                      // 1931
      var beginswith = []                                                                                           // 1932
        , caseSensitive = []                                                                                        // 1933
        , caseInsensitive = []                                                                                      // 1934
        , item                                                                                                      // 1935
                                                                                                                    // 1936
      while (item = items.shift()) {                                                                                // 1937
        if (!item.toLowerCase().indexOf(this.query.toLowerCase())) beginswith.push(item)                            // 1938
        else if (~item.indexOf(this.query)) caseSensitive.push(item)                                                // 1939
        else caseInsensitive.push(item)                                                                             // 1940
      }                                                                                                             // 1941
                                                                                                                    // 1942
      return beginswith.concat(caseSensitive, caseInsensitive)                                                      // 1943
    }                                                                                                               // 1944
                                                                                                                    // 1945
  , highlighter: function (item) {                                                                                  // 1946
      var query = this.query.replace(/[\-\[\]{}()*+?.,\\\^$|#\s]/g, '\\$&')                                         // 1947
      return item.replace(new RegExp('(' + query + ')', 'ig'), function ($1, match) {                               // 1948
        return '<strong>' + match + '</strong>'                                                                     // 1949
      })                                                                                                            // 1950
    }                                                                                                               // 1951
                                                                                                                    // 1952
  , render: function (items) {                                                                                      // 1953
      var that = this                                                                                               // 1954
                                                                                                                    // 1955
      items = $(items).map(function (i, item) {                                                                     // 1956
        i = $(that.options.item).attr('data-value', item)                                                           // 1957
        i.find('a').html(that.highlighter(item))                                                                    // 1958
        return i[0]                                                                                                 // 1959
      })                                                                                                            // 1960
                                                                                                                    // 1961
      items.first().addClass('active')                                                                              // 1962
      this.$menu.html(items)                                                                                        // 1963
      return this                                                                                                   // 1964
    }                                                                                                               // 1965
                                                                                                                    // 1966
  , next: function (event) {                                                                                        // 1967
      var active = this.$menu.find('.active').removeClass('active')                                                 // 1968
        , next = active.next()                                                                                      // 1969
                                                                                                                    // 1970
      if (!next.length) {                                                                                           // 1971
        next = $(this.$menu.find('li')[0])                                                                          // 1972
      }                                                                                                             // 1973
                                                                                                                    // 1974
      next.addClass('active')                                                                                       // 1975
    }                                                                                                               // 1976
                                                                                                                    // 1977
  , prev: function (event) {                                                                                        // 1978
      var active = this.$menu.find('.active').removeClass('active')                                                 // 1979
        , prev = active.prev()                                                                                      // 1980
                                                                                                                    // 1981
      if (!prev.length) {                                                                                           // 1982
        prev = this.$menu.find('li').last()                                                                         // 1983
      }                                                                                                             // 1984
                                                                                                                    // 1985
      prev.addClass('active')                                                                                       // 1986
    }                                                                                                               // 1987
                                                                                                                    // 1988
  , listen: function () {                                                                                           // 1989
      this.$element                                                                                                 // 1990
        .on('focus',    $.proxy(this.focus, this))                                                                  // 1991
        .on('blur',     $.proxy(this.blur, this))                                                                   // 1992
        .on('keypress', $.proxy(this.keypress, this))                                                               // 1993
        .on('keyup',    $.proxy(this.keyup, this))                                                                  // 1994
                                                                                                                    // 1995
      if (this.eventSupported('keydown')) {                                                                         // 1996
        this.$element.on('keydown', $.proxy(this.keydown, this))                                                    // 1997
      }                                                                                                             // 1998
                                                                                                                    // 1999
      this.$menu                                                                                                    // 2000
        .on('click', $.proxy(this.click, this))                                                                     // 2001
        .on('mouseenter', 'li', $.proxy(this.mouseenter, this))                                                     // 2002
        .on('mouseleave', 'li', $.proxy(this.mouseleave, this))                                                     // 2003
    }                                                                                                               // 2004
                                                                                                                    // 2005
  , eventSupported: function(eventName) {                                                                           // 2006
      var isSupported = eventName in this.$element                                                                  // 2007
      if (!isSupported) {                                                                                           // 2008
        this.$element.setAttribute(eventName, 'return;')                                                            // 2009
        isSupported = typeof this.$element[eventName] === 'function'                                                // 2010
      }                                                                                                             // 2011
      return isSupported                                                                                            // 2012
    }                                                                                                               // 2013
                                                                                                                    // 2014
  , move: function (e) {                                                                                            // 2015
      if (!this.shown) return                                                                                       // 2016
                                                                                                                    // 2017
      switch(e.keyCode) {                                                                                           // 2018
        case 9: // tab                                                                                              // 2019
        case 13: // enter                                                                                           // 2020
        case 27: // escape                                                                                          // 2021
          e.preventDefault()                                                                                        // 2022
          break                                                                                                     // 2023
                                                                                                                    // 2024
        case 38: // up arrow                                                                                        // 2025
          e.preventDefault()                                                                                        // 2026
          this.prev()                                                                                               // 2027
          break                                                                                                     // 2028
                                                                                                                    // 2029
        case 40: // down arrow                                                                                      // 2030
          e.preventDefault()                                                                                        // 2031
          this.next()                                                                                               // 2032
          break                                                                                                     // 2033
      }                                                                                                             // 2034
                                                                                                                    // 2035
      e.stopPropagation()                                                                                           // 2036
    }                                                                                                               // 2037
                                                                                                                    // 2038
  , keydown: function (e) {                                                                                         // 2039
      this.suppressKeyPressRepeat = ~$.inArray(e.keyCode, [40,38,9,13,27])                                          // 2040
      this.move(e)                                                                                                  // 2041
    }                                                                                                               // 2042
                                                                                                                    // 2043
  , keypress: function (e) {                                                                                        // 2044
      if (this.suppressKeyPressRepeat) return                                                                       // 2045
      this.move(e)                                                                                                  // 2046
    }                                                                                                               // 2047
                                                                                                                    // 2048
  , keyup: function (e) {                                                                                           // 2049
      switch(e.keyCode) {                                                                                           // 2050
        case 40: // down arrow                                                                                      // 2051
        case 38: // up arrow                                                                                        // 2052
        case 16: // shift                                                                                           // 2053
        case 17: // ctrl                                                                                            // 2054
        case 18: // alt                                                                                             // 2055
          break                                                                                                     // 2056
                                                                                                                    // 2057
        case 9: // tab                                                                                              // 2058
        case 13: // enter                                                                                           // 2059
          if (!this.shown) return                                                                                   // 2060
          this.select()                                                                                             // 2061
          break                                                                                                     // 2062
                                                                                                                    // 2063
        case 27: // escape                                                                                          // 2064
          if (!this.shown) return                                                                                   // 2065
          this.hide()                                                                                               // 2066
          break                                                                                                     // 2067
                                                                                                                    // 2068
        default:                                                                                                    // 2069
          this.lookup()                                                                                             // 2070
      }                                                                                                             // 2071
                                                                                                                    // 2072
      e.stopPropagation()                                                                                           // 2073
      e.preventDefault()                                                                                            // 2074
  }                                                                                                                 // 2075
                                                                                                                    // 2076
  , focus: function (e) {                                                                                           // 2077
      this.focused = true                                                                                           // 2078
    }                                                                                                               // 2079
                                                                                                                    // 2080
  , blur: function (e) {                                                                                            // 2081
      this.focused = false                                                                                          // 2082
      if (!this.mousedover && this.shown) this.hide()                                                               // 2083
    }                                                                                                               // 2084
                                                                                                                    // 2085
  , click: function (e) {                                                                                           // 2086
      e.stopPropagation()                                                                                           // 2087
      e.preventDefault()                                                                                            // 2088
      this.select()                                                                                                 // 2089
      this.$element.focus()                                                                                         // 2090
    }                                                                                                               // 2091
                                                                                                                    // 2092
  , mouseenter: function (e) {                                                                                      // 2093
      this.mousedover = true                                                                                        // 2094
      this.$menu.find('.active').removeClass('active')                                                              // 2095
      $(e.currentTarget).addClass('active')                                                                         // 2096
    }                                                                                                               // 2097
                                                                                                                    // 2098
  , mouseleave: function (e) {                                                                                      // 2099
      this.mousedover = false                                                                                       // 2100
      if (!this.focused && this.shown) this.hide()                                                                  // 2101
    }                                                                                                               // 2102
                                                                                                                    // 2103
  }                                                                                                                 // 2104
                                                                                                                    // 2105
                                                                                                                    // 2106
  /* TYPEAHEAD PLUGIN DEFINITION                                                                                    // 2107
   * =========================== */                                                                                 // 2108
                                                                                                                    // 2109
  var old = $.fn.typeahead                                                                                          // 2110
                                                                                                                    // 2111
  $.fn.typeahead = function (option) {                                                                              // 2112
    return this.each(function () {                                                                                  // 2113
      var $this = $(this)                                                                                           // 2114
        , data = $this.data('typeahead')                                                                            // 2115
        , options = typeof option == 'object' && option                                                             // 2116
      if (!data) $this.data('typeahead', (data = new Typeahead(this, options)))                                     // 2117
      if (typeof option == 'string') data[option]()                                                                 // 2118
    })                                                                                                              // 2119
  }                                                                                                                 // 2120
                                                                                                                    // 2121
  $.fn.typeahead.defaults = {                                                                                       // 2122
    source: []                                                                                                      // 2123
  , items: 8                                                                                                        // 2124
  , menu: '<ul class="typeahead dropdown-menu"></ul>'                                                               // 2125
  , item: '<li><a href="#"></a></li>'                                                                               // 2126
  , minLength: 1                                                                                                    // 2127
  }                                                                                                                 // 2128
                                                                                                                    // 2129
  $.fn.typeahead.Constructor = Typeahead                                                                            // 2130
                                                                                                                    // 2131
                                                                                                                    // 2132
 /* TYPEAHEAD NO CONFLICT                                                                                           // 2133
  * =================== */                                                                                          // 2134
                                                                                                                    // 2135
  $.fn.typeahead.noConflict = function () {                                                                         // 2136
    $.fn.typeahead = old                                                                                            // 2137
    return this                                                                                                     // 2138
  }                                                                                                                 // 2139
                                                                                                                    // 2140
                                                                                                                    // 2141
 /* TYPEAHEAD DATA-API                                                                                              // 2142
  * ================== */                                                                                           // 2143
                                                                                                                    // 2144
  $(document).on('focus.typeahead.data-api', '[data-provide="typeahead"]', function (e) {                           // 2145
    var $this = $(this)                                                                                             // 2146
    if ($this.data('typeahead')) return                                                                             // 2147
    $this.typeahead($this.data())                                                                                   // 2148
  })                                                                                                                // 2149
                                                                                                                    // 2150
}(window.jQuery);                                                                                                   // 2151
/* ==========================================================                                                       // 2152
 * bootstrap-affix.js v2.3.0                                                                                        // 2153
 * http://twitter.github.com/bootstrap/javascript.html#affix                                                        // 2154
 * ==========================================================                                                       // 2155
 * Copyright 2012 Twitter, Inc.                                                                                     // 2156
 *                                                                                                                  // 2157
 * Licensed under the Apache License, Version 2.0 (the "License");                                                  // 2158
 * you may not use this file except in compliance with the License.                                                 // 2159
 * You may obtain a copy of the License at                                                                          // 2160
 *                                                                                                                  // 2161
 * http://www.apache.org/licenses/LICENSE-2.0                                                                       // 2162
 *                                                                                                                  // 2163
 * Unless required by applicable law or agreed to in writing, software                                              // 2164
 * distributed under the License is distributed on an "AS IS" BASIS,                                                // 2165
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.                                         // 2166
 * See the License for the specific language governing permissions and                                              // 2167
 * limitations under the License.                                                                                   // 2168
 * ========================================================== */                                                    // 2169
                                                                                                                    // 2170
                                                                                                                    // 2171
!function ($) {                                                                                                     // 2172
                                                                                                                    // 2173
  "use strict"; // jshint ;_;                                                                                       // 2174
                                                                                                                    // 2175
                                                                                                                    // 2176
 /* AFFIX CLASS DEFINITION                                                                                          // 2177
  * ====================== */                                                                                       // 2178
                                                                                                                    // 2179
  var Affix = function (element, options) {                                                                         // 2180
    this.options = $.extend({}, $.fn.affix.defaults, options)                                                       // 2181
    this.$window = $(window)                                                                                        // 2182
      .on('scroll.affix.data-api', $.proxy(this.checkPosition, this))                                               // 2183
      .on('click.affix.data-api',  $.proxy(function () { setTimeout($.proxy(this.checkPosition, this), 1) }, this)) // 2184
    this.$element = $(element)                                                                                      // 2185
    this.checkPosition()                                                                                            // 2186
  }                                                                                                                 // 2187
                                                                                                                    // 2188
  Affix.prototype.checkPosition = function () {                                                                     // 2189
    if (!this.$element.is(':visible')) return                                                                       // 2190
                                                                                                                    // 2191
    var scrollHeight = $(document).height()                                                                         // 2192
      , scrollTop = this.$window.scrollTop()                                                                        // 2193
      , position = this.$element.offset()                                                                           // 2194
      , offset = this.options.offset                                                                                // 2195
      , offsetBottom = offset.bottom                                                                                // 2196
      , offsetTop = offset.top                                                                                      // 2197
      , reset = 'affix affix-top affix-bottom'                                                                      // 2198
      , affix                                                                                                       // 2199
                                                                                                                    // 2200
    if (typeof offset != 'object') offsetBottom = offsetTop = offset                                                // 2201
    if (typeof offsetTop == 'function') offsetTop = offset.top()                                                    // 2202
    if (typeof offsetBottom == 'function') offsetBottom = offset.bottom()                                           // 2203
                                                                                                                    // 2204
    affix = this.unpin != null && (scrollTop + this.unpin <= position.top) ?                                        // 2205
      false    : offsetBottom != null && (position.top + this.$element.height() >= scrollHeight - offsetBottom) ?   // 2206
      'bottom' : offsetTop != null && scrollTop <= offsetTop ?                                                      // 2207
      'top'    : false                                                                                              // 2208
                                                                                                                    // 2209
    if (this.affixed === affix) return                                                                              // 2210
                                                                                                                    // 2211
    this.affixed = affix                                                                                            // 2212
    this.unpin = affix == 'bottom' ? position.top - scrollTop : null                                                // 2213
                                                                                                                    // 2214
    this.$element.removeClass(reset).addClass('affix' + (affix ? '-' + affix : ''))                                 // 2215
  }                                                                                                                 // 2216
                                                                                                                    // 2217
                                                                                                                    // 2218
 /* AFFIX PLUGIN DEFINITION                                                                                         // 2219
  * ======================= */                                                                                      // 2220
                                                                                                                    // 2221
  var old = $.fn.affix                                                                                              // 2222
                                                                                                                    // 2223
  $.fn.affix = function (option) {                                                                                  // 2224
    return this.each(function () {                                                                                  // 2225
      var $this = $(this)                                                                                           // 2226
        , data = $this.data('affix')                                                                                // 2227
        , options = typeof option == 'object' && option                                                             // 2228
      if (!data) $this.data('affix', (data = new Affix(this, options)))                                             // 2229
      if (typeof option == 'string') data[option]()                                                                 // 2230
    })                                                                                                              // 2231
  }                                                                                                                 // 2232
                                                                                                                    // 2233
  $.fn.affix.Constructor = Affix                                                                                    // 2234
                                                                                                                    // 2235
  $.fn.affix.defaults = {                                                                                           // 2236
    offset: 0                                                                                                       // 2237
  }                                                                                                                 // 2238
                                                                                                                    // 2239
                                                                                                                    // 2240
 /* AFFIX NO CONFLICT                                                                                               // 2241
  * ================= */                                                                                            // 2242
                                                                                                                    // 2243
  $.fn.affix.noConflict = function () {                                                                             // 2244
    $.fn.affix = old                                                                                                // 2245
    return this                                                                                                     // 2246
  }                                                                                                                 // 2247
                                                                                                                    // 2248
                                                                                                                    // 2249
 /* AFFIX DATA-API                                                                                                  // 2250
  * ============== */                                                                                               // 2251
                                                                                                                    // 2252
  $(window).on('load', function () {                                                                                // 2253
    $('[data-spy="affix"]').each(function () {                                                                      // 2254
      var $spy = $(this)                                                                                            // 2255
        , data = $spy.data()                                                                                        // 2256
                                                                                                                    // 2257
      data.offset = data.offset || {}                                                                               // 2258
                                                                                                                    // 2259
      data.offsetBottom && (data.offset.bottom = data.offsetBottom)                                                 // 2260
      data.offsetTop && (data.offset.top = data.offsetTop)                                                          // 2261
                                                                                                                    // 2262
      $spy.affix(data)                                                                                              // 2263
    })                                                                                                              // 2264
  })                                                                                                                // 2265
                                                                                                                    // 2266
                                                                                                                    // 2267
}(window.jQuery);                                                                                                   // 2268
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);


/* Exports */
if (typeof Package === 'undefined') Package = {};
Package.bootstrap = {};

})();

//# sourceMappingURL=86f8f0d5d5a274fd05c4a35c7a7dddb771ce2a0e.map
