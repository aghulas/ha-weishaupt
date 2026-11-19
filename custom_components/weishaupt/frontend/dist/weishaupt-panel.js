var F=globalThis,K=F.ShadowRoot&&(F.ShadyCSS===void 0||F.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,te=Symbol(),be=new WeakMap,N=class{constructor(s,t,e){if(this._$cssResult$=!0,e!==te)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=s,this.t=t}get styleSheet(){let s=this.o,t=this.t;if(K&&s===void 0){let e=t!==void 0&&t.length===1;e&&(s=be.get(t)),s===void 0&&((this.o=s=new CSSStyleSheet).replaceSync(this.cssText),e&&be.set(t,s))}return s}toString(){return this.cssText}},$e=a=>new N(typeof a=="string"?a:a+"",void 0,te),se=(a,...s)=>{let t=a.length===1?a[0]:s.reduce((e,r,i)=>e+(n=>{if(n._$cssResult$===!0)return n.cssText;if(typeof n=="number")return n;throw Error("Value passed to 'css' function must be a 'css' function result: "+n+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(r)+a[i+1],a[0]);return new N(t,a,te)},ye=(a,s)=>{if(K)a.adoptedStyleSheets=s.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(let t of s){let e=document.createElement("style"),r=F.litNonce;r!==void 0&&e.setAttribute("nonce",r),e.textContent=t.cssText,a.appendChild(e)}},re=K?a=>a:a=>a instanceof CSSStyleSheet?(s=>{let t="";for(let e of s.cssRules)t+=e.cssText;return $e(t)})(a):a;var{is:Qe,defineProperty:Ze,getOwnPropertyDescriptor:et,getOwnPropertyNames:tt,getOwnPropertySymbols:st,getPrototypeOf:rt}=Object,J=globalThis,ve=J.trustedTypes,it=ve?ve.emptyScript:"",nt=J.reactiveElementPolyfillSupport,O=(a,s)=>a,ie={toAttribute(a,s){switch(s){case Boolean:a=a?it:null;break;case Object:case Array:a=a==null?a:JSON.stringify(a)}return a},fromAttribute(a,s){let t=a;switch(s){case Boolean:t=a!==null;break;case Number:t=a===null?null:Number(a);break;case Object:case Array:try{t=JSON.parse(a)}catch{t=null}}return t}},xe=(a,s)=>!Qe(a,s),we={attribute:!0,type:String,converter:ie,reflect:!1,useDefault:!1,hasChanged:xe};Symbol.metadata??=Symbol("metadata"),J.litPropertyMetadata??=new WeakMap;var v=class extends HTMLElement{static addInitializer(s){this._$Ei(),(this.l??=[]).push(s)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(s,t=we){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(s)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(s,t),!t.noAccessor){let e=Symbol(),r=this.getPropertyDescriptor(s,e,t);r!==void 0&&Ze(this.prototype,s,r)}}static getPropertyDescriptor(s,t,e){let{get:r,set:i}=et(this.prototype,s)??{get(){return this[t]},set(n){this[t]=n}};return{get:r,set(n){let d=r?.call(this);i?.call(this,n),this.requestUpdate(s,d,e)},configurable:!0,enumerable:!0}}static getPropertyOptions(s){return this.elementProperties.get(s)??we}static _$Ei(){if(this.hasOwnProperty(O("elementProperties")))return;let s=rt(this);s.finalize(),s.l!==void 0&&(this.l=[...s.l]),this.elementProperties=new Map(s.elementProperties)}static finalize(){if(this.hasOwnProperty(O("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(O("properties"))){let t=this.properties,e=[...tt(t),...st(t)];for(let r of e)this.createProperty(r,t[r])}let s=this[Symbol.metadata];if(s!==null){let t=litPropertyMetadata.get(s);if(t!==void 0)for(let[e,r]of t)this.elementProperties.set(e,r)}this._$Eh=new Map;for(let[t,e]of this.elementProperties){let r=this._$Eu(t,e);r!==void 0&&this._$Eh.set(r,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(s){let t=[];if(Array.isArray(s)){let e=new Set(s.flat(1/0).reverse());for(let r of e)t.unshift(re(r))}else s!==void 0&&t.push(re(s));return t}static _$Eu(s,t){let e=t.attribute;return e===!1?void 0:typeof e=="string"?e:typeof s=="string"?s.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(s=>this.enableUpdating=s),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(s=>s(this))}addController(s){(this._$EO??=new Set).add(s),this.renderRoot!==void 0&&this.isConnected&&s.hostConnected?.()}removeController(s){this._$EO?.delete(s)}_$E_(){let s=new Map,t=this.constructor.elementProperties;for(let e of t.keys())this.hasOwnProperty(e)&&(s.set(e,this[e]),delete this[e]);s.size>0&&(this._$Ep=s)}createRenderRoot(){let s=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return ye(s,this.constructor.elementStyles),s}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(s=>s.hostConnected?.())}enableUpdating(s){}disconnectedCallback(){this._$EO?.forEach(s=>s.hostDisconnected?.())}attributeChangedCallback(s,t,e){this._$AK(s,e)}_$ET(s,t){let e=this.constructor.elementProperties.get(s),r=this.constructor._$Eu(s,e);if(r!==void 0&&e.reflect===!0){let i=(e.converter?.toAttribute!==void 0?e.converter:ie).toAttribute(t,e.type);this._$Em=s,i==null?this.removeAttribute(r):this.setAttribute(r,i),this._$Em=null}}_$AK(s,t){let e=this.constructor,r=e._$Eh.get(s);if(r!==void 0&&this._$Em!==r){let i=e.getPropertyOptions(r),n=typeof i.converter=="function"?{fromAttribute:i.converter}:i.converter?.fromAttribute!==void 0?i.converter:ie;this._$Em=r;let d=n.fromAttribute(t,i.type);this[r]=d??this._$Ej?.get(r)??d,this._$Em=null}}requestUpdate(s,t,e,r=!1,i){if(s!==void 0){let n=this.constructor;if(r===!1&&(i=this[s]),e??=n.getPropertyOptions(s),!((e.hasChanged??xe)(i,t)||e.useDefault&&e.reflect&&i===this._$Ej?.get(s)&&!this.hasAttribute(n._$Eu(s,e))))return;this.C(s,t,e)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(s,t,{useDefault:e,reflect:r,wrapped:i},n){e&&!(this._$Ej??=new Map).has(s)&&(this._$Ej.set(s,n??t??this[s]),i!==!0||n!==void 0)||(this._$AL.has(s)||(this.hasUpdated||e||(t=void 0),this._$AL.set(s,t)),r===!0&&this._$Em!==s&&(this._$Eq??=new Set).add(s))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}let s=this.scheduleUpdate();return s!=null&&await s,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[r,i]of this._$Ep)this[r]=i;this._$Ep=void 0}let e=this.constructor.elementProperties;if(e.size>0)for(let[r,i]of e){let{wrapped:n}=i,d=this[r];n!==!0||this._$AL.has(r)||d===void 0||this.C(r,void 0,i,d)}}let s=!1,t=this._$AL;try{s=this.shouldUpdate(t),s?(this.willUpdate(t),this._$EO?.forEach(e=>e.hostUpdate?.()),this.update(t)):this._$EM()}catch(e){throw s=!1,this._$EM(),e}s&&this._$AE(t)}willUpdate(s){}_$AE(s){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(s)),this.updated(s)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(s){return!0}update(s){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(s){}firstUpdated(s){}};v.elementStyles=[],v.shadowRootOptions={mode:"open"},v[O("elementProperties")]=new Map,v[O("finalized")]=new Map,nt?.({ReactiveElement:v}),(J.reactiveElementVersions??=[]).push("2.1.2");var ue=globalThis,ke=a=>a,X=ue.trustedTypes,Ae=X?X.createPolicy("lit-html",{createHTML:a=>a}):void 0,Te="$lit$",k=`lit$${Math.random().toFixed(9).slice(2)}$`,Pe="?"+k,at=`<${Pe}>`,C=document,L=()=>C.createComment(""),q=a=>a===null||typeof a!="object"&&typeof a!="function",he=Array.isArray,ot=a=>he(a)||typeof a?.[Symbol.iterator]=="function",ne=`[ 	
\f\r]`,U=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,Ee=/-->/g,Se=/>/g,S=RegExp(`>|${ne}(?:([^\\s"'>=/]+)(${ne}*=${ne}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),Re=/'/g,Ce=/"/g,De=/^(?:script|style|textarea|title)$/i,pe=a=>(s,...t)=>({_$litType$:a,strings:s,values:t}),l=pe(1),mt=pe(2),bt=pe(3),M=Symbol.for("lit-noChange"),u=Symbol.for("lit-nothing"),Me=new WeakMap,R=C.createTreeWalker(C,129);function He(a,s){if(!he(a)||!a.hasOwnProperty("raw"))throw Error("invalid template strings array");return Ae!==void 0?Ae.createHTML(s):s}var dt=(a,s)=>{let t=a.length-1,e=[],r,i=s===2?"<svg>":s===3?"<math>":"",n=U;for(let d=0;d<t;d++){let c=a[d],h,_,p=-1,b=0;for(;b<c.length&&(n.lastIndex=b,_=n.exec(c),_!==null);)b=n.lastIndex,n===U?_[1]==="!--"?n=Ee:_[1]!==void 0?n=Se:_[2]!==void 0?(De.test(_[2])&&(r=RegExp("</"+_[2],"g")),n=S):_[3]!==void 0&&(n=S):n===S?_[0]===">"?(n=r??U,p=-1):_[1]===void 0?p=-2:(p=n.lastIndex-_[2].length,h=_[1],n=_[3]===void 0?S:_[3]==='"'?Ce:Re):n===Ce||n===Re?n=S:n===Ee||n===Se?n=U:(n=S,r=void 0);let y=n===S&&a[d+1].startsWith("/>")?" ":"";i+=n===U?c+at:p>=0?(e.push(h),c.slice(0,p)+Te+c.slice(p)+k+y):c+k+(p===-2?d:y)}return[He(a,i+(a[t]||"<?>")+(s===2?"</svg>":s===3?"</math>":"")),e]},j=class a{constructor({strings:s,_$litType$:t},e){let r;this.parts=[];let i=0,n=0,d=s.length-1,c=this.parts,[h,_]=dt(s,t);if(this.el=a.createElement(h,e),R.currentNode=this.el.content,t===2||t===3){let p=this.el.content.firstChild;p.replaceWith(...p.childNodes)}for(;(r=R.nextNode())!==null&&c.length<d;){if(r.nodeType===1){if(r.hasAttributes())for(let p of r.getAttributeNames())if(p.endsWith(Te)){let b=_[n++],y=r.getAttribute(p).split(k),w=/([.?@])?(.*)/.exec(b);c.push({type:1,index:i,name:w[2],strings:y,ctor:w[1]==="."?oe:w[1]==="?"?de:w[1]==="@"?le:D}),r.removeAttribute(p)}else p.startsWith(k)&&(c.push({type:6,index:i}),r.removeAttribute(p));if(De.test(r.tagName)){let p=r.textContent.split(k),b=p.length-1;if(b>0){r.textContent=X?X.emptyScript:"";for(let y=0;y<b;y++)r.append(p[y],L()),R.nextNode(),c.push({type:2,index:++i});r.append(p[b],L())}}}else if(r.nodeType===8)if(r.data===Pe)c.push({type:2,index:i});else{let p=-1;for(;(p=r.data.indexOf(k,p+1))!==-1;)c.push({type:7,index:i}),p+=k.length-1}i++}}static createElement(s,t){let e=C.createElement("template");return e.innerHTML=s,e}};function P(a,s,t=a,e){if(s===M)return s;let r=e!==void 0?t._$Co?.[e]:t._$Cl,i=q(s)?void 0:s._$litDirective$;return r?.constructor!==i&&(r?._$AO?.(!1),i===void 0?r=void 0:(r=new i(a),r._$AT(a,t,e)),e!==void 0?(t._$Co??=[])[e]=r:t._$Cl=r),r!==void 0&&(s=P(a,r._$AS(a,s.values),r,e)),s}var ae=class{constructor(s,t){this._$AV=[],this._$AN=void 0,this._$AD=s,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(s){let{el:{content:t},parts:e}=this._$AD,r=(s?.creationScope??C).importNode(t,!0);R.currentNode=r;let i=R.nextNode(),n=0,d=0,c=e[0];for(;c!==void 0;){if(n===c.index){let h;c.type===2?h=new I(i,i.nextSibling,this,s):c.type===1?h=new c.ctor(i,c.name,c.strings,this,s):c.type===6&&(h=new ce(i,this,s)),this._$AV.push(h),c=e[++d]}n!==c?.index&&(i=R.nextNode(),n++)}return R.currentNode=C,r}p(s){let t=0;for(let e of this._$AV)e!==void 0&&(e.strings!==void 0?(e._$AI(s,e,t),t+=e.strings.length-2):e._$AI(s[t])),t++}},I=class a{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(s,t,e,r){this.type=2,this._$AH=u,this._$AN=void 0,this._$AA=s,this._$AB=t,this._$AM=e,this.options=r,this._$Cv=r?.isConnected??!0}get parentNode(){let s=this._$AA.parentNode,t=this._$AM;return t!==void 0&&s?.nodeType===11&&(s=t.parentNode),s}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(s,t=this){s=P(this,s,t),q(s)?s===u||s==null||s===""?(this._$AH!==u&&this._$AR(),this._$AH=u):s!==this._$AH&&s!==M&&this._(s):s._$litType$!==void 0?this.$(s):s.nodeType!==void 0?this.T(s):ot(s)?this.k(s):this._(s)}O(s){return this._$AA.parentNode.insertBefore(s,this._$AB)}T(s){this._$AH!==s&&(this._$AR(),this._$AH=this.O(s))}_(s){this._$AH!==u&&q(this._$AH)?this._$AA.nextSibling.data=s:this.T(C.createTextNode(s)),this._$AH=s}$(s){let{values:t,_$litType$:e}=s,r=typeof e=="number"?this._$AC(s):(e.el===void 0&&(e.el=j.createElement(He(e.h,e.h[0]),this.options)),e);if(this._$AH?._$AD===r)this._$AH.p(t);else{let i=new ae(r,this),n=i.u(this.options);i.p(t),this.T(n),this._$AH=i}}_$AC(s){let t=Me.get(s.strings);return t===void 0&&Me.set(s.strings,t=new j(s)),t}k(s){he(this._$AH)||(this._$AH=[],this._$AR());let t=this._$AH,e,r=0;for(let i of s)r===t.length?t.push(e=new a(this.O(L()),this.O(L()),this,this.options)):e=t[r],e._$AI(i),r++;r<t.length&&(this._$AR(e&&e._$AB.nextSibling,r),t.length=r)}_$AR(s=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);s!==this._$AB;){let e=ke(s).nextSibling;ke(s).remove(),s=e}}setConnected(s){this._$AM===void 0&&(this._$Cv=s,this._$AP?.(s))}},D=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(s,t,e,r,i){this.type=1,this._$AH=u,this._$AN=void 0,this.element=s,this.name=t,this._$AM=r,this.options=i,e.length>2||e[0]!==""||e[1]!==""?(this._$AH=Array(e.length-1).fill(new String),this.strings=e):this._$AH=u}_$AI(s,t=this,e,r){let i=this.strings,n=!1;if(i===void 0)s=P(this,s,t,0),n=!q(s)||s!==this._$AH&&s!==M,n&&(this._$AH=s);else{let d=s,c,h;for(s=i[0],c=0;c<i.length-1;c++)h=P(this,d[e+c],t,c),h===M&&(h=this._$AH[c]),n||=!q(h)||h!==this._$AH[c],h===u?s=u:s!==u&&(s+=(h??"")+i[c+1]),this._$AH[c]=h}n&&!r&&this.j(s)}j(s){s===u?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,s??"")}},oe=class extends D{constructor(){super(...arguments),this.type=3}j(s){this.element[this.name]=s===u?void 0:s}},de=class extends D{constructor(){super(...arguments),this.type=4}j(s){this.element.toggleAttribute(this.name,!!s&&s!==u)}},le=class extends D{constructor(s,t,e,r,i){super(s,t,e,r,i),this.type=5}_$AI(s,t=this){if((s=P(this,s,t,0)??u)===M)return;let e=this._$AH,r=s===u&&e!==u||s.capture!==e.capture||s.once!==e.once||s.passive!==e.passive,i=s!==u&&(e===u||r);r&&this.element.removeEventListener(this.name,this,e),i&&this.element.addEventListener(this.name,this,s),this._$AH=s}handleEvent(s){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,s):this._$AH.handleEvent(s)}},ce=class{constructor(s,t,e){this.element=s,this.type=6,this._$AN=void 0,this._$AM=t,this.options=e}get _$AU(){return this._$AM._$AU}_$AI(s){P(this,s)}};var lt=ue.litHtmlPolyfillSupport;lt?.(j,I),(ue.litHtmlVersions??=[]).push("3.3.3");var Ne=(a,s,t)=>{let e=t?.renderBefore??s,r=e._$litPart$;if(r===void 0){let i=t?.renderBefore??null;e._$litPart$=r=new I(s.insertBefore(L(),i),i,void 0,t??{})}return r._$AI(a),r};var _e=globalThis,A=class extends v{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let s=super.createRenderRoot();return this.renderOptions.renderBefore??=s.firstChild,s}update(s){let t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(s),this._$Do=Ne(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return M}};A._$litElement$=!0,A.finalized=!0,_e.litElementHydrateSupport?.({LitElement:A});var ct=_e.litElementPolyfillSupport;ct?.({LitElement:A});(_e.litElementVersions??=[]).push("4.2.2");var Le="-",ge={en:{title:"Weishaupt",installation:"Installation",devices:"Devices",definitions:"Definitions",programs:"Weekly programs",loading:"Loading\u2026",no_installation:"No Weishaupt installation is loaded.",unavailable:"ebusd does not answer: the values shown are the last ones read.",value:"Value",name:"Name",age:"Read",range:"Range",write:"Write",entity:"Entity",open:"Open",comfort:"comfort",regulation:"regulation",read_only:"read only",not_loaded:"not loaded by ebusd",not_listened:"not read: no enabled entity",waiting:"waiting for the first reading",not_available:"not available",seconds_ago:"{n} s ago",minutes_ago:"{n} min ago",hours_ago:"{n} h ago",days_ago:"{n} d ago",passive:"sent by the device",clock_offset:"Clock master",clock_line:"{label}: {text}",clock_ahead:"{n} s ahead",clock_behind:"{n} s behind",clock_on_time:"on time",software:"Software",hardware:"Hardware",address:"Bus address",in_use:"In use",source_bundled:"shipped with the integration",source_file:"file beside the configuration: {file}",refused:"Files not used",mismatches:"Differences with ebusd",named_from_metadata:"Entities named from the definitions",not_named:"Entities waiting for a name",messages:"Messages",usable:"{usable} of {messages} loaded by ebusd as described",writes:"Writes",writes_off:"disabled in the options",switch_on:"switch on",switch_off:"switch off",capability:"run-time checksum: {value}",per_hour:"{n} of {max} this hour",ebusd:"ebusd",unknown_addresses:"Addresses answering that no definition knows",none:"none",day_unread:"not read yet",day_none:"no range",editable:"editable through its program-day entities",not_editable:"read only: not proven writable on this device",not_read_program:"not loaded by ebusd",program_not_listened:"not read by any enabled entity: read it once now, or enable the program sensor to keep it up to date",write_hint:"Change a setting with its button Change (the writes switch must be on). Comfort: written at once and read back; regulation: after a confirmation in this panel. Open shows the entity.",description:"Description",no_sensor:"no sensor",kept:"kept from before the reload, read again soon",through:"through {circuit}",read_now:"Read now",read_cost:"{n} requests to the bus, about {s} s, once",read_queued:"{n} requests queued; the grid fills in as they are answered",readable:"{usable} of {readable} readable messages loaded by ebusd as described",not_usable:"Messages not read",reason_write_only:"write only",reason_device_absent:"device not on the bus",absent_circuit:"{circuit}: {n} messages, device not on the bus",reason_mismatch:"not loaded as described",reason_other:"not read",disabled:"disabled",reloading:"The integration was reloaded: loading again\u2026",read_only_settings:"Settings left read-only",edit:"Change",write_now:"Write",cancel:"Cancel",confirm:"Write to the controller",confirm_clock:"Send the time",confirm_title:"Confirm: {setting} \u2014 {device}",current:"Current value",new_value:"New value",allowed:"Allowed",path:"Written to bus address {address}, register {register}, from source address {source} ({source_text}). Read back right after.",path_short:"bus address {address}, register {register}, from {source}",regulation_note:"This setting changes how the heating is regulated: it is written after your confirmation.",comfort_note:"Comfort setting: written at once and read back.",writing:"Writing\u2026",written_line:"{before} \u2192 {after}{frame}: {result}",not_written:"Not written: {message}",not_offered_writes_disabled:"writes are not enabled in the options",not_offered:"not offered on this installation: {reason}",switch_off_hint:"The writes switch is off: turn it on to write.",edit_days:"Edit",write_days:"Write the changed days",discard:"Discard changes",copy_to:"Copy to",copy:"Copy",cost:"{days} days changed: up to {writes} writes (only changed slots are written); {used} of {max} this hour",cost_one:"1 day changed: up to {writes} writes (only changed slots are written); {used} of {max} this hour",interrupted:"no answer from Home Assistant (connection interrupted): the write may or may not have been sent; check the value read back",drag_hint:"Type the ranges, or drag on the bar to add one in quarters of an hour; a click on a range removes it.",day_format:"use HH:MM-HH:MM, up to three ranges, or -",day_quarter:"times must be quarters of an hour, from 00:00 to 24:00",day_order:"a range must end after it starts",day_too_many:"at most three ranges",day_overlap:"ranges must not overlap",set_clock:"Set the clock",clock_confirm:"Will send Home Assistant's time at second 00 of the next minute ({send_at}), to bus address fe from source address 31. If the bus is not free within {late} s of second 00, nothing is sent.",clock_sent:"Sent {requested} ({frame}): {result}",clock_current:"Clock master now: {current}"},fr:{title:"Weishaupt",installation:"Installation",devices:"Appareils",definitions:"D\xE9finitions",programs:"Programmes hebdomadaires",loading:"Chargement\u2026",no_installation:"Aucune installation Weishaupt n'est charg\xE9e.",unavailable:"ebusd ne r\xE9pond pas : les valeurs affich\xE9es sont les derni\xE8res lues.",value:"Valeur",name:"Nom",age:"Lu",range:"Plage",write:"\xC9criture",entity:"Entit\xE9",open:"Ouvrir",comfort:"confort",regulation:"r\xE9gulation",read_only:"lecture seule",not_loaded:"non charg\xE9 par ebusd",not_listened:"non lu : aucune entit\xE9 activ\xE9e",waiting:"en attente de la premi\xE8re lecture",not_available:"non disponible",seconds_ago:"il y a {n} s",minutes_ago:"il y a {n} min",hours_ago:"il y a {n} h",days_ago:"il y a {n} j",passive:"envoy\xE9 par l'appareil",clock_offset:"Horloge ma\xEEtresse",clock_line:"{label} : {text}",clock_ahead:"{n} s d'avance",clock_behind:"{n} s de retard",clock_on_time:"\xE0 l'heure",software:"Logiciel",hardware:"Mat\xE9riel",address:"Adresse de bus",in_use:"Utilis\xE9es",source_bundled:"livr\xE9es avec l'int\xE9gration",source_file:"fichier \xE0 c\xF4t\xE9 de la configuration : {file}",refused:"Fichiers non utilis\xE9s",mismatches:"\xC9carts avec ebusd",named_from_metadata:"Entit\xE9s nomm\xE9es par les d\xE9finitions",not_named:"Entit\xE9s en attente d'un nom",messages:"Messages",usable:"{usable} sur {messages} charg\xE9s par ebusd comme d\xE9crits",writes:"\xC9critures",writes_off:"d\xE9sactiv\xE9es dans les options",switch_on:"interrupteur allum\xE9",switch_off:"interrupteur \xE9teint",capability:"checksum \xE0 l'ex\xE9cution : {value}",per_hour:"{n} sur {max} cette heure",ebusd:"ebusd",unknown_addresses:"Adresses qui r\xE9pondent sans d\xE9finition",none:"aucun",day_unread:"pas encore lu",day_none:"aucune plage",editable:"modifiable par ses entit\xE9s de jour de programme",not_editable:"lecture seule : \xE9criture non prouv\xE9e sur cet appareil",not_read_program:"non charg\xE9 par ebusd",program_not_listened:"lu par aucune entit\xE9 activ\xE9e : lisez-le une fois maintenant, ou activez le capteur du programme pour le tenir \xE0 jour",write_hint:"Modifiez un r\xE9glage avec son bouton Modifier (l'interrupteur d'\xE9criture doit \xEAtre allum\xE9). Confort : \xE9crit aussit\xF4t et relu ; r\xE9gulation : apr\xE8s une confirmation dans ce panneau. Ouvrir affiche l'entit\xE9.",description:"Description",no_sensor:"pas de sonde",kept:"conserv\xE9e d'avant le rechargement, relue bient\xF4t",through:"par {circuit}",read_now:"Lire maintenant",read_cost:"{n} requ\xEAtes sur le bus, environ {s} s, une seule fois",read_queued:"{n} requ\xEAtes en file ; la grille se remplit au fil des r\xE9ponses",readable:"{usable} sur {readable} messages lisibles charg\xE9s par ebusd comme d\xE9crits",not_usable:"Messages non lus",reason_write_only:"\xE9criture seule",reason_device_absent:"appareil absent du bus",absent_circuit:"{circuit} : {n} messages, appareil absent du bus",reason_mismatch:"non charg\xE9 comme d\xE9crit",reason_other:"non lu",disabled:"d\xE9sactiv\xE9e",reloading:"L'int\xE9gration a \xE9t\xE9 recharg\xE9e : nouveau chargement\u2026",read_only_settings:"R\xE9glages laiss\xE9s en lecture seule",edit:"Modifier",write_now:"\xC9crire",cancel:"Annuler",confirm:"\xC9crire dans le r\xE9gulateur",confirm_clock:"Envoyer l'heure",confirm_title:"Confirmer : {setting} \u2014 {device}",current:"Valeur actuelle",new_value:"Nouvelle valeur",allowed:"Valeurs autoris\xE9es",path:"\xC9crit \xE0 l'adresse de bus {address}, registre {register}, depuis l'adresse source {source} ({source_text}). Relu juste apr\xE8s.",path_short:"adresse de bus {address}, registre {register}, depuis {source}",regulation_note:"Ce r\xE9glage modifie la r\xE9gulation du chauffage : il est \xE9crit apr\xE8s votre confirmation.",comfort_note:"R\xE9glage de confort : \xE9crit aussit\xF4t et relu.",writing:"\xC9criture\u2026",written_line:"{before} \u2192 {after}{frame} : {result}",not_written:"Non \xE9crit : {message}",not_offered_writes_disabled:"l'\xE9criture n'est pas activ\xE9e dans les options",not_offered:"non propos\xE9 sur cette installation : {reason}",switch_off_hint:"L'interrupteur d'\xE9criture est \xE9teint : allumez-le pour \xE9crire.",edit_days:"Modifier",write_days:"\xC9crire les jours modifi\xE9s",discard:"Abandonner les modifications",copy_to:"Copier vers",copy:"Copier",cost:"{days} jours modifi\xE9s : jusqu'\xE0 {writes} \xE9critures (seuls les cr\xE9neaux chang\xE9s sont \xE9crits) ; {used} sur {max} cette heure",cost_one:"1 jour modifi\xE9 : jusqu'\xE0 {writes} \xE9critures (seuls les cr\xE9neaux chang\xE9s sont \xE9crits) ; {used} sur {max} cette heure",interrupted:"pas de r\xE9ponse de Home Assistant (connexion interrompue) : l'\xE9criture a pu partir ou non ; v\xE9rifiez la valeur relue",drag_hint:"Saisissez les plages, ou glissez sur la barre pour en ajouter une au quart d'heure ; un clic sur une plage la retire.",day_format:"\xE9crivez HH:MM-HH:MM, trois plages au plus, ou -",day_quarter:"les heures doivent \xEAtre des quarts d'heure, de 00:00 \xE0 24:00",day_order:"une plage doit finir apr\xE8s son d\xE9but",day_too_many:"trois plages au plus",day_overlap:"les plages ne doivent pas se chevaucher",set_clock:"Mettre \xE0 l'heure",clock_confirm:"Enverra l'heure de Home Assistant \xE0 la seconde 00 de la minute suivante ({send_at}), \xE0 l'adresse de bus fe depuis l'adresse source 31. Si le bus n'est pas libre dans les {late} s apr\xE8s la seconde 00, rien n'est envoy\xE9.",clock_sent:"Envoy\xE9 {requested} ({frame}) : {result}",clock_current:"Horloge ma\xEEtresse maintenant : {current}"}},W={en:["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],fr:["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]};function qe(a){let s=(a??"en").split("-")[0];return s in ge?s:"en"}function o(a,s,t={}){return(ge[a]?.[s]??ge.en[s]??s).replace(/\{(\w+)\}/g,(r,i)=>String(t[i]??`{${i}}`))}function g(a,s){return a?a[s]??a.en??Object.values(a)[0]??"":""}function me(a,s,t){if(!s)return null;let e=s.values[a.index];if(e===void 0)return null;if(e===Le)return o(t,"not_available");if(a.absent!==null&&a.absent!==void 0&&Number(e)===a.absent)return o(t,"no_sensor");if(a.values){let r=a.values[e];return r?g(r,t):e}return a.unit?`${e} ${a.unit}`:e}function je(a,s){let t=e=>e.split(" (")[0].trim().toLowerCase();return!a||t(a)===t(s)}function G(a,s){for(let t of a.messages??[a.message]){let e=s[t];if(e)return e}return null}function Ie(a,s){let t=new Map,e=[];for(let r of a)if(r.reason==="device_absent"){let i=r.key.split("/")[0];t.set(i,(t.get(i)??0)+1)}else e.push(`${r.key}: ${o(s,`reason_${r.reason}`)}`);for(let[r,i]of t)e.push(o(s,"absent_circuit",{circuit:r,n:i}));return e}function We(a,s){let t=s?.values[a.index];if(t===void 0||t===""||t===Le)return"";let e=a.writable?.options;if(e){let r=e.find(i=>i.name===t);return r?String(r.raw):""}return Number.isNaN(Number(t))?"":t}function ze(a){return a.read?!a.entity_id&&!a.passive?"not_listened":"waiting":"not_loaded"}function Be(a,s){let t=Math.max(0,Math.round(a));return t<90?o(s,"seconds_ago",{n:t}):t<90*60?o(s,"minutes_ago",{n:Math.round(t/60)}):t<36*3600?o(s,"hours_ago",{n:Math.round(t/3600)}):o(s,"days_ago",{n:Math.round(t/86400)})}function Ve(a){let s=a.range;if(!s)return"";let t=a.unit?` ${a.unit}`:"",e=`${s.min??"\u2026"} \u2013 ${s.max??"\u2026"}${t}`;return s.step?`${e} (${s.step})`:e}var Fe=3,fe=15;function H(a){let s=a.trim();if(s===""||s==="-")return{ranges:[]};let t=[];for(let e of s.split(",")){let r=/^\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*$/.exec(e);if(!r)return{error:"day_format"};let[i,n,d,c]=r.slice(1).map(Number),h=i*60+n,_=d*60+c;if([n,c].some(p=>p%fe)||h>1440||_>1440||n>45||c>45)return{error:"day_quarter"};if(h>=_)return{error:"day_order"};t.push([h,_])}if(t.length>Fe)return{error:"day_too_many"};t.sort((e,r)=>e[0]-r[0]);for(let e=1;e<t.length;e++)if(t[e][0]<t[e-1][1])return{error:"day_overlap"};return{ranges:t}}function Oe(a){let s=Math.floor(a/60),t=a%60;return`${String(s).padStart(2,"0")}:${String(t).padStart(2,"0")}`}function z(a){return a.length?a.map(([s,t])=>`${Oe(s)}-${Oe(t)}`).join(", "):"-"}function Ke(a,s,t){let e=c=>Math.round(Math.min(1,Math.max(0,c))*1440/fe)*fe,r=Math.min(e(s),e(t)),i=Math.max(e(s),e(t));i===r&&(i=Math.min(1440,r+60));let n=[];for(let[c,h]of a)c<=i&&h>=r?(r=Math.min(r,c),i=Math.max(i,h)):n.push([c,h]);let d=[...n,[r,i]].sort((c,h)=>c[0]-h[0]);return d.length>Fe?null:d}function Ue(a){let[s,t]=a.split(":").map(e=>Number(e));return s*60+(t||0)}function Je(a){return a.map(([s,t])=>{let e=Ue(s),r=Ue(t);return{left:e/1440*100,width:Math.max(0,r-e)/1440*100,text:`${s}-${t}`}})}function Y(a){let s=[],t=(e,r)=>{for(let i of a.filter(n=>n.parent===e))s.push([i,r]),t(i.id,r+1)};t("",0);for(let e of a)s.some(([r])=>r.id===e.id)||s.push([e,0]);return s}var Q="__definitions__";function ut(a,s,t){let e=a.find(r=>r.id===s)?.parent??"";for(;e;){if(e===t)return!0;e=a.find(r=>r.id===e)?.parent??""}return!1}var ht="programs",B=class extends A{constructor(){super();this._offset=0;this._readings={},this._programs={},this._available=!0,this._tick=0,this._queued={},this._reloading=!1,this._draft="",this._rowResult={},this._busy=!1,this._weekDraft={},this._weekResult={}}get _lang(){return qe(this.hass?.language)}connectedCallback(){super.connectedCallback(),this._timer=window.setInterval(()=>this._tick+=1,3e4),this._entryId&&this._subscribe(this._entryId)}disconnectedCallback(){super.disconnectedCallback(),window.clearInterval(this._timer),this._unsubscribe?.(),this._unsubscribe=void 0}willUpdate(t){t.has("hass")&&this.hass&&this._installations===void 0&&!this._loading&&(this._loading="installations",this.hass.callWS({type:"weishaupt/panel/installations"}).then(e=>{this._installations=e,e.length&&this._select(e[0].entry_id)}).catch(e=>this._error=e.message))}async _select(t,e=!1){this._entryId=t,e||(this._tree=void 0,this._device=void 0,this._menu=void 0),this._readings={},this._programs={},this._queued={};try{let r=await this.hass.callWS({type:"weishaupt/panel/tree",entry_id:t});this._tree=r,r.devices.some(i=>i.id===this._device)||(this._device=r.devices[0]?.id,this._menu=r.devices[0]?.menus[0]?.id),await this._subscribe(t)}catch(r){if(e)throw r;this._error=r.message}}async _readProgram(t){if(!this._entryId)return;let e=await this.hass.callWS({type:"weishaupt/panel/read_program",entry_id:this._entryId,program:t});this._queued={...this._queued,[t]:e.queued}}async _subscribe(t){this._unsubscribe?.(),this._unsubscribe=await this.hass.connection.subscribeMessage(e=>this._live(e),{type:"weishaupt/panel/subscribe",entry_id:t})}_live(t){if(this._offset=Date.now()/1e3-t.now,t.reloaded){this._unsubscribe=void 0,this._reloading=!0;let e=r=>{window.setTimeout(()=>{!this._entryId||!this.isConnected||this._select(this._entryId,!0).then(()=>this._reloading=!1,()=>r>0?e(r-1):this._error=o(this._lang,"reloading"))},2e3)};e(15);return}t.available!==void 0&&(this._available=t.available),t.readings&&(this._readings={...this._readings,...t.readings}),t.programs&&(this._programs={...this._programs,...t.programs})}_open(t){this.dispatchEvent(new CustomEvent("hass-more-info",{detail:{entityId:t},bubbles:!0,composed:!0}))}_age(t){return Be(Date.now()/1e3-this._offset-t.when,this._lang)}render(){let t=this._lang;return this._error?l`<div class="message error" role="alert">${this._error}</div>`:this._installations===void 0?l`<div class="message">${o(t,"loading")}</div>`:this._installations.length?l`
      <header>
        <h1>${o(t,"title")}</h1>
        ${this._installations.length>1?l`<label
              >${o(t,"installation")}
              <select @change=${e=>this._select(e.target.value)}>
                ${this._installations.map(e=>l`<option value=${e.entry_id} ?selected=${e.entry_id===this._entryId}>${e.title}</option>`)}
              </select></label
            >`:u}
        ${this._clock()}
        ${this._tree?.writes?.clock_writable?l`<button class="link" ?disabled=${this._busy} @click=${()=>this._setClock()}>
              ${o(t,"set_clock")}
            </button>`:u}
        ${this._rowResult.__clock__?l`<span class=${this._rowResult.__clock__.error?"error":"secondary"} role="status"
              >${this._rowResult.__clock__.text}</span
            >`:u}
      </header>
      ${this._available?u:l`<div class="message warning" role="status">${o(t,"unavailable")}</div>`}
      ${this._reloading?l`<div class="message" role="status">${o(t,"reloading")}</div>`:u}
      ${this._tree?this._body(this._tree):l`<div class="message">${o(t,"loading")}</div>`}
      ${this._dialog?this._confirmDialog(this._dialog.answer):u}
    `:l`<div class="message">${o(t,"no_installation")}</div>`}async _call(t){this._busy=!0;try{let e=await this.hass.callWS({...t,entry_id:this._entryId,language:this._lang});return e.guard&&this._tree?.writes&&(this._tree={...this._tree,writes:{...this._tree.writes,...e.guard}}),e}catch(e){let r=e,i=!r?.code||r.code==="connection_lost"||/connection/i.test(r.message??"");return{status:"refused",code:i?"interrupted":r.code,message:i?o(this._lang,"interrupted"):r.message||r.code}}finally{this._busy=!1}}_switchOn(){let t=this._tree?.writes;if(!t)return!1;let e=t.switch_entity_id?this.hass.states[t.switch_entity_id]:void 0;return e?e.state==="on":t.switch}_resultText(t){let e=this._lang;return t.status==="refused"?{text:o(e,"not_written",{message:t.message??""}),error:!0}:t.kind==="clock"||t.requested!==void 0?{text:o(e,"clock_sent",{requested:t.requested??"",frame:t.frame??"",result:t.result_text??t.result??""}),error:t.result!=="sent"}:{text:o(e,"written_line",{before:t.before??"-",after:t.after??"",frame:t.frame?` (${t.frame})`:"",result:t.result_text??t.result??""}),error:t.result!=="ok"&&t.result!=="unchanged"}}_writing(t){this._rowResult={...this._rowResult,[t]:{text:o(this._lang,"writing"),error:!1}}}async _writeRow(t){let e=t.writable,r=Number(this._draft);this._writing(t.key);let i=await this._call({type:"weishaupt/panel/write",key:e.key,value:r});this._handle(i,t.key),i.status!=="refused"&&(this._editing=void 0)}_handle(t,e){if(t.status==="confirm"){this._dialog={answer:t,target:e};return}this._rowResult={...this._rowResult,[e]:this._resultText(t)}}async _setClock(){this._writing("__clock__"),this._handle(await this._call({type:"weishaupt/panel/clock"}),"__clock__")}async _confirmed(){let t=this._dialog;this._dialog=void 0,this._writing(t.target);let e=await this._call({type:"weishaupt/panel/confirm",pending_id:t.answer.pending_id});this._rowResult={...this._rowResult,[t.target]:this._resultText(e)}}async _withdrawn(){let t=this._dialog;this._dialog=void 0;let e={...this._rowResult};delete e[t.target],this._rowResult=e,await this._call({type:"weishaupt/panel/cancel",pending_id:t.answer.pending_id})}_confirmDialog(t){let e=this._lang,r=t.placeholders??{},i=t.kind==="clock";return l`<div class="backdrop">
      <div class="dialog" role="dialog" aria-modal="true" aria-labelledby="confirm-title"
        @keydown=${n=>n.key==="Escape"&&this._withdrawn()}>
        <h2 id="confirm-title">${o(e,"confirm_title",{setting:r.setting??"",device:r.device??""})}</h2>
        ${i?l`<p>${o(e,"clock_current",{current:r.current??"-"})}</p>
              <p>${o(e,"clock_confirm",{send_at:r.send_at??"",late:r.late??""})}</p>`:l`<dl>
                <dt>${o(e,"current")}</dt>
                <dd>${r.current}</dd>
                <dt>${o(e,"new_value")}</dt>
                <dd><strong>${r.requested}</strong></dd>
                <dt>${o(e,"allowed")}</dt>
                <dd>${r.allowed}</dd>
              </dl>
              <p>${o(e,"path",r)}</p>
              <p class="secondary">${o(e,"regulation_note")}</p>`}
        <div class="actions">
          <button class="link" @click=${()=>this._withdrawn()}>${o(e,"cancel")}</button>
          <button class="primary" autofocus @click=${()=>this._confirmed()}>
            ${o(e,i?"confirm_clock":"confirm")}
          </button>
        </div>
      </div>
    </div>`}_writeCell(t){let e=this._lang,r=t.writable;if(!r)return l`<span class="secondary">${o(e,"read_only")}</span>`;let i=this._rowResult[t.key],n=l`<span class="badge ${r.risk}">${o(e,r.risk)}</span>${r.through?l`<div class="secondary">${o(e,"through",{circuit:r.through})}</div>`:u}`,d=u;return r.offered?this._editing===t.key?d=u:d=l`<button class="link" @click=${()=>this._startEdit(t)}>${o(e,"edit")}</button>`:d=l`<div class="secondary">
        ${r.why_not==="writes_disabled"?o(e,"not_offered_writes_disabled"):o(e,"not_offered",{reason:r.why_not??""})}
      </div>`,l`${n}${d}${i?l`<div class=${i.error?"error":"secondary"} role="status">${i.text}</div>`:u}`}_editForm(t){let e=this._lang,r=t.writable,i=G(t,this._readings);return l`<form
        class="edit"
        @submit=${n=>{n.preventDefault(),this._writeRow(t)}}
      >
        ${r.options?l`<select aria-label=${o(e,"new_value")}
              @change=${n=>this._draft=n.target.value}>
              <option value="" ?selected=${this._draft===""} disabled>…</option>
              ${r.options.map(n=>l`<option value=${n.raw} ?selected=${String(n.raw)===this._draft}>${g(n.label,e)}</option>`)}
            </select>`:l`<input type="number" aria-label=${o(e,"new_value")} .value=${this._draft}
              min=${r.minimum??""} max=${r.maximum??""} step=${r.step??"any"}
              @input=${n=>this._draft=n.target.value} />${t.unit?l` ${t.unit}`:u}`}
        <button class="primary" type="submit" ?disabled=${this._busy||this._draft===""}>${o(e,"write_now")}</button>
        <button class="link" type="button" @click=${()=>this._editing=void 0}>${o(e,"cancel")}</button>
        <div class="secondary">
          ${me(t,i,e)??"-"} ·
          ${o(e,"path_short",{address:r.address??"",register:r.register??"",source:r.source})}
        </div>
        <div class="secondary">${o(e,r.risk==="comfort"?"comfort_note":"regulation_note")}</div>
        ${this._tree?.writes&&!this._switchOn()?l`<div class="error">${o(e,"switch_off_hint")}</div>`:u}
      </form>`}_startEdit(t){this._draft=We(t,G(t,this._readings)),this._editing=t.key}_dayText(t,e){let r=t?.[e];return r==null?null:z(r.map(([i,n])=>[Xe(i),Xe(n)]))}_startWeek(t){let e=this._programs[t.key],r={};for(let i=1;i<=7;i++)r[String(i)]=this._dayText(e,String(i))??"";this._weekDraft={...this._weekDraft,[t.key]:r},this._weekResult={...this._weekResult,[t.key]:void 0}}_setDay(t,e,r){this._weekDraft={...this._weekDraft,[t]:{...this._weekDraft[t],[e]:r}}}_changed(t){let e=this._weekDraft[t.key]??{},r=this._programs[t.key];return Object.keys(e).filter(i=>{let n=this._dayText(r,i);if(n===null&&e[i].trim()==="")return!1;let d=H(e[i]);return("ranges"in d?z(d.ranges):e[i])!==n})}async _writeWeek(t){let e=this._weekDraft[t.key],r={};for(let _ of this._changed(t))r[_]=e[_];this._weekResult={...this._weekResult,[t.key]:{text:o(this._lang,"writing"),error:!1}};let i=await this._call({type:"weishaupt/panel/write_days",program:t.key,days:r}),n=this._lang;if(i.status==="refused"){this._weekResult={...this._weekResult,[t.key]:this._resultText(i)};return}let d=W[n]??W.en,c=Object.entries(i.days??{}).map(([_,p])=>o(n,"written_line",{before:`${d[Number(_)-1]} ${p.before??"-"}`,after:p.after??"",frame:p.frames?.length?` (${p.frames.join(", ")})`:"",result:p.result_text??p.result??""}));this._weekResult={...this._weekResult,[t.key]:{text:c.join(" \xB7 "),error:!1}};let h={...this._weekDraft};delete h[t.key],this._weekDraft=h}_copy(t,e,r){let i=this._weekDraft[t][e],n=r==="all"?["1","2","3","4","5","6","7"]:r==="weekdays"?["1","2","3","4","5"]:r==="weekend"?["6","7"]:[r],d={...this._weekDraft[t]};for(let c of n)c!==e&&(d[c]=i);this._weekDraft={...this._weekDraft,[t]:d}}_dragStart(t,e,r){let i=t.currentTarget;if(t.target.classList.contains("bar"))return;let n=i.getBoundingClientRect();this._drag={program:e,day:r,from:(t.clientX-n.left)/n.width,element:i},i.setPointerCapture(t.pointerId)}_dragEnd(t){let e=this._drag;if(this._drag=void 0,!e)return;let r=e.element.getBoundingClientRect(),i=H(this._weekDraft[e.program][e.day]);if(!("ranges"in i))return;let n=Ke(i.ranges,e.from,(t.clientX-r.left)/r.width);n&&this._setDay(e.program,e.day,z(n))}_removeRange(t,e,r){let i=H(this._weekDraft[t][e]);"ranges"in i&&this._setDay(t,e,z(i.ranges.filter((n,d)=>d!==r)))}_clock(){let t=this._tree?.clock.entity_id,e=t?this.hass.states[t]:void 0;if(!t||!e||Number.isNaN(Number(e.state)))return u;let r=this._lang,i=Math.round(Number(e.state)),n=i===0?o(r,"clock_on_time"):o(r,i>0?"clock_ahead":"clock_behind",{n:Math.abs(i)});return l`<button class="clock link" @click=${()=>this._open(t)}>
      ${o(r,"clock_line",{label:o(r,"clock_offset"),text:n})}
    </button>`}_body(t){let e=t.devices.find(r=>r.id===this._device);return l`<div class=${this.narrow?"layout narrow":"layout"}>
      <nav aria-label=${o(this._lang,"devices")}>${this._nav(t)}</nav>
      <main>${this._menu===Q?this._definitions(t):e?this._device_view(e):u}</main>
    </div>`}_nav(t){let e=this._lang;if(this.narrow){let i=`${this._device??""}|${this._menu??""}`;return l`<label class="choose"
        >${o(e,"devices")}
        <select
          @change=${n=>{let[d,c]=n.target.value.split("|");this._device=d,this._menu=c}}
        >
          ${t.devices.map(n=>l`<optgroup label=${g(n.label,e)}>
              ${Y(n.menus).map(([d,c])=>l`<option value=${`${n.id}|${d.id}`} ?selected=${i===`${n.id}|${d.id}`}>
                    ${"\xA0\xA0".repeat(c)}${g(d.label,e)}
                  </option>`)}
            </optgroup>`)}
          <option value=${`${this._device??""}|${Q}`} ?selected=${this._menu===Q}>
            ${o(e,"definitions")}
          </option>
        </select></label
      >`}let r=(i,n,d,c)=>{let h=this._device===i&&this._menu===n;return l`<li>
        <button
          class="menu depth${c}"
          aria-current=${h?"page":"false"}
          @click=${()=>{this._device=i,this._menu=n}}
        >
          ${d}
        </button>
      </li>`};return l`<ul>
      ${t.devices.map(i=>l`<li>
          <span class="device">${g(i.label,e)}</span>
          <ul>
            ${Y(i.menus).map(([n,d])=>r(i.id,n.id,g(n.label,e),d))}
          </ul>
        </li>`)}
      ${r(this._device??"",Q,o(e,"definitions"),0)}
    </ul>`}_device_view(t){let e=this._lang,r=t.menus.find(d=>d.id===this._menu),i=[t.addresses.length?`${o(e,"address")} ${t.addresses.join(", ")}`:"",t.software?`${o(e,"software")} ${t.software}`:"",t.hardware?`${o(e,"hardware")} ${t.hardware}`:""].filter(Boolean),n=Y(t.menus).filter(([d])=>d.id===this._menu||ut(t.menus,d.id,this._menu??"")).map(([d])=>[d,t.rows.filter(c=>c.menu===d.id)]).filter(([,d])=>d.length);return l`<h2>${g(t.label,e)}${r?l` — ${g(r.label,e)}`:u}</h2>
      ${i.length?l`<p class="secondary">${i.join(" \xB7 ")}</p>`:u}
      ${this._menu===ht?this._programs_view(t):u}
      ${n.length?l`<p class="secondary">${o(e,"write_hint")}</p>`:u}
      ${n.map(([d,c])=>l`${d.id!==this._menu?l`<h3>${g(d.label,e)}</h3>`:u}${this._table(c)}`)}`}_table(t){let e=this._lang;return this._tick,l`<div class="scroll">
        <table>
          <thead>
            <tr>
              <th scope="col">${o(e,"name")}</th>
              <th scope="col">${o(e,"value")}</th>
              <th scope="col">${o(e,"age")}</th>
              <th scope="col">${o(e,"range")}</th>
              <th scope="col">${o(e,"write")}</th>
              <th scope="col">${o(e,"entity")}</th>
            </tr>
          </thead>
          <tbody>
            ${t.map(r=>{let i=G(r,this._readings),n=me(r,i,e),d=je(g(r.description,e),g(r.label,e))?"":g(r.description,e);return l`<tr>
                <th scope="row">
                  ${g(r.label,e)}
                  ${d?l`<div class="description">${d}</div>`:u}
                </th>
                <td class="nowrap">${n??l`<span class="secondary">${o(e,ze(r))}</span>`}</td>
                <td class="secondary nowrap">
                  ${i?this._age(i):""}${i?.kept?l`<div class="kept">${o(e,"kept")}</div>`:u}${r.passive?l`<div>${o(e,"passive")}</div>`:u}
                </td>
                <td class="nowrap">${Ve(r)}</td>
                <td>${this._writeCell(r)}</td>
                <td>
                  ${r.entity_id?l`<button class="link" @click=${()=>this._open(r.entity_id)}>${o(e,"open")}</button>`:u}
                </td>
              </tr>${this._editing===r.key?l`<tr class="edit-row"><td colspan="6">${this._editForm(r)}</td></tr>`:u}`})}
          </tbody>
        </table>
      </div>`}_programs_view(t){let e=this._lang,r=W[e]??W.en,i=this._tree?.writes;return l`${t.programs.map(n=>{let d=this._programs[n.key],c=this._weekDraft[n.key],h=c!==void 0,_=h?this._changed(n):[],p=h?Object.fromEntries(Object.entries(c).map(([$,V])=>{let f=H(V);return[$,"error"in f?f.error:null]})):{},b=Object.values(p).some(Boolean),y=n.read?n.listened?n.writable?o(e,"editable"):o(e,"not_editable"):o(e,"program_not_listened"):o(e,"not_read_program"),w=this._weekResult[n.key];return l`<section class="program">
        <h3>
          ${g(n.label,e)}
          ${n.entity_id?l`<button class="link" @click=${()=>this._open(n.entity_id)}>${o(e,"open")}</button>`:u}
          ${n.writable&&i&&!h?l`<button class="link" @click=${()=>this._startWeek(n)}>${o(e,"edit_days")}</button>`:u}
        </h3>
        <p class="secondary">${y}</p>
        ${n.read&&!n.listened?this._queued[n.key]!==void 0?l`<p class="secondary" role="status">${o(e,"read_queued",{n:this._queued[n.key]})}</p>`:l`<p>
                <button class="link" @click=${()=>this._readProgram(n.key)}>${o(e,"read_now")}</button>
                <span class="secondary"
                  >${o(e,"read_cost",{n:n.slots,s:Math.round(n.slots*2.2)})}</span
                >
              </p>`:u}
        ${h?l`<p class="secondary">${o(e,"drag_hint")}</p>`:u}
        <table class="week">
          <caption class="visually-hidden">${g(n.label,e)}</caption>
          <thead>
            <tr>
              <th scope="col"><span class="visually-hidden">${o(e,"programs")}</span></th>
              <td class="scale" aria-hidden="true">
                ${[0,6,12,18,24].map($=>l`<span style="left:${$/24*100}%">${$}</span>`)}
              </td>
            </tr>
          </thead>
          <tbody>
            ${r.map(($,V)=>{let f=String(V+1);if(h){let E=H(c[f]),Z="ranges"in E?E.ranges:[],ee=p[f];return l`<tr class=${_.includes(f)?"changed":""}>
                  <th scope="row">${$}</th>
                  <td>
                    <div
                      class="day editable"
                      aria-hidden="true"
                      @pointerdown=${m=>this._dragStart(m,n.key,f)}
                      @pointerup=${m=>this._dragEnd(m)}
                    >
                      ${Z.map(([m,x],Ye)=>l`<span
                          class="bar"
                          style="left:${m/1440*100}%;width:${(x-m)/1440*100}%"
                          @click=${()=>this._removeRange(n.key,f,Ye)}
                        ></span>`)}
                    </div>
                    <div class="day-edit">
                      <input
                        type="text"
                        aria-label=${$}
                        aria-invalid=${ee?"true":"false"}
                        placeholder=${d?.[f]==null?o(e,"day_unread"):""}
                        .value=${c[f]}
                        @input=${m=>this._setDay(n.key,f,m.target.value)}
                      />
                      <label class="secondary"
                        >${o(e,"copy_to")}
                        <select
                          @change=${m=>{let x=m.target;x.value&&this._copy(n.key,f,x.value),x.value=""}}
                        >
                          <option value="">…</option>
                          <option value="all">${e==="fr"?"tous les jours":"every day"}</option>
                          <option value="weekdays">${e==="fr"?"lundi \u2013 vendredi":"Monday \u2013 Friday"}</option>
                          <option value="weekend">${e==="fr"?"samedi, dimanche":"Saturday, Sunday"}</option>
                          ${r.map((m,x)=>x===V?u:l`<option value=${String(x+1)}>${m}</option>`)}
                        </select></label
                      >
                    </div>
                    ${ee?l`<div class="error" role="alert">${o(e,ee)}</div>`:u}
                  </td>
                </tr>`}let T=d?.[f],Ge=T==null?o(e,n.listened?"day_unread":"not_listened"):T.length?T.map(([E,Z])=>`${E}-${Z}`).join(", "):o(e,"day_none");return l`<tr>
                <th scope="row">${$}</th>
                <td>
                  <div class="day" aria-hidden="true">
                    ${(T??[]).length?Je(T).map(E=>l`<span class="bar" style="left:${E.left}%;width:${E.width}%"></span>`):u}
                  </div>
                  <div class="day-text">${Ge}</div>
                </td>
              </tr>`})}
          </tbody>
        </table>
        ${h&&i?l`<p class="secondary">
                ${o(e,_.length===1?"cost_one":"cost",{days:_.length,writes:_.length*3,used:i.writes_last_hour,max:i.max_per_hour})}
              </p>
              ${this._switchOn()?u:l`<p class="error">${o(e,"switch_off_hint")}</p>`}
              <div class="actions">
                <button class="link" @click=${()=>{let $={...this._weekDraft};delete $[n.key],this._weekDraft=$}}>${o(e,"discard")}</button>
                <button class="primary" ?disabled=${this._busy||b||!_.length}
                  @click=${()=>this._writeWeek(n)}>${o(e,"write_days")}</button>
              </div>`:u}
        ${w?l`<p class=${w.error?"error":"secondary"} role="status">${w.text}</p>`:u}
      </section>`})}`}_definitions(t){let e=this._lang,r=t.definitions,i=d=>d.length?l`<ul>${d.map(c=>l`<li><code>${c}</code></li>`)}</ul>`:l`${o(e,"none")}`,n=t.writes;return l`<h2>${o(e,"definitions")}</h2>
      <dl>
        <dt>${o(e,"in_use")}</dt>
        <dd>
          ${r.version}${r.commit?l` <code>${r.commit.slice(0,7)}</code>`:u} —
          ${r.source==="bundled"?o(e,"source_bundled"):o(e,"source_file",{file:r.source})}
        </dd>
        <dt>${o(e,"messages")}</dt>
        <dd>
          ${o(e,"readable",{usable:r.usable,readable:r.usable+r.not_usable.filter(d=>d.reason==="mismatch"||d.reason==="other").length})}
        </dd>
        <dt>${o(e,"not_usable")}</dt>
        <dd>${i(Ie(r.not_usable,e))}</dd>
        <dt>${o(e,"refused")}</dt>
        <dd>${i(Object.entries(r.refused).map(([d,c])=>`${d}: ${c}`))}</dd>
        <dt>${o(e,"mismatches")}</dt>
        <dd>${i(r.mismatches.map(d=>`${d.key}: ${d.reason}${d.detail?` (${d.detail})`:""}`))}</dd>
        <dt>${o(e,"named_from_metadata")}</dt>
        <dd>
          ${i(r.named_from_metadata.map(d=>d.disabled?`${d.entity_id} (${o(e,"disabled")})`:d.entity_id))}
        </dd>
        <dt>${o(e,"not_named")}</dt>
        <dd>${i(r.not_named)}</dd>
        <dt>${o(e,"ebusd")}</dt>
        <dd>${t.ebusd.version??"?"}${t.ebusd.own_address?` (${t.ebusd.own_address})`:""}</dd>
        <dt>${o(e,"unknown_addresses")}</dt>
        <dd>${i(t.unknown_addresses)}</dd>
        <dt>${o(e,"writes")}</dt>
        <dd>
          ${n?l`${o(e,this._switchOn()?"switch_on":"switch_off")} ·
              ${o(e,"capability",{value:n.capability})} ·
              ${o(e,"per_hour",{n:n.writes_last_hour,max:n.max_per_hour})}`:o(e,"writes_off")}
        </dd>
        ${n?l`<dt>${o(e,"read_only_settings")}</dt>
              <dd>${i(n.read_only.map(d=>`${d.key}: ${d.reason}`))}</dd>`:u}
      </dl>`}};B.properties={hass:{attribute:!1},narrow:{type:Boolean},_installations:{state:!0},_entryId:{state:!0},_tree:{state:!0},_readings:{state:!0},_programs:{state:!0},_available:{state:!0},_device:{state:!0},_menu:{state:!0},_error:{state:!0},_tick:{state:!0},_queued:{state:!0},_reloading:{state:!0},_editing:{state:!0},_draft:{state:!0},_rowResult:{state:!0},_busy:{state:!0},_dialog:{state:!0},_weekDraft:{state:!0},_weekResult:{state:!0}},B.styles=se`
    :host {
      display: block;
      min-height: 100vh;
      background: var(--primary-background-color);
      color: var(--primary-text-color);
      font-family: var(--paper-font-body1_-_font-family, inherit);
    }
    header {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 12px 24px;
      padding: 12px 16px;
      background: var(--app-header-background-color, var(--card-background-color));
      color: var(--app-header-text-color, var(--primary-text-color));
      border-bottom: 1px solid var(--divider-color);
    }
    h1 {
      font-size: 20px;
      font-weight: 400;
      margin: 0;
    }
    h2 {
      font-size: 18px;
      font-weight: 500;
      margin: 0 0 8px;
    }
    h3 {
      font-size: 16px;
      font-weight: 500;
      margin: 16px 0 4px;
    }
    .layout {
      display: grid;
      grid-template-columns: minmax(200px, 260px) 1fr;
      gap: 16px;
      padding: 16px;
    }
    .layout.narrow {
      grid-template-columns: 1fr;
    }
    nav,
    main {
      background: var(--card-background-color);
      border-radius: var(--ha-card-border-radius, 12px);
      border: 1px solid var(--divider-color);
      padding: 12px;
      min-width: 0;
    }
    nav ul {
      list-style: none;
      margin: 0;
      padding: 0;
    }
    label.choose {
      display: flex;
      flex-direction: column;
      gap: 4px;
      color: var(--secondary-text-color);
    }
    select {
      font: inherit;
      padding: 6px;
      color: var(--primary-text-color);
      background: var(--card-background-color);
      border: 1px solid var(--divider-color);
      border-radius: 6px;
    }
    .device {
      display: block;
      font-weight: 500;
      margin: 12px 0 4px;
    }
    button {
      font: inherit;
      color: inherit;
    }
    button.menu {
      display: block;
      width: 100%;
      text-align: start;
      border: 0;
      background: none;
      padding: 6px 8px;
      border-radius: 6px;
      cursor: pointer;
    }
    button.menu.depth1 {
      padding-inline-start: 24px;
    }
    button.menu.depth2 {
      padding-inline-start: 40px;
    }
    button.menu[aria-current="page"] {
      background: var(--secondary-background-color);
      color: var(--primary-color);
      font-weight: 500;
    }
    button:focus-visible {
      outline: 2px solid var(--primary-color);
      outline-offset: 2px;
    }
    button.link {
      border: 1px solid var(--divider-color);
      background: none;
      border-radius: 6px;
      padding: 2px 8px;
      cursor: pointer;
      color: var(--primary-color);
    }
    .nowrap {
      white-space: nowrap;
    }
    .scroll {
      overflow-x: auto;
    }
    table {
      border-collapse: collapse;
      width: 100%;
    }
    th,
    td {
      text-align: start;
      vertical-align: top;
      padding: 6px 8px;
      border-bottom: 1px solid var(--divider-color);
    }
    thead th {
      font-weight: 500;
      color: var(--secondary-text-color);
    }
    tbody th {
      font-weight: 400;
      min-width: 12em;
    }
    .description,
    .secondary {
      color: var(--secondary-text-color);
      font-size: 0.9em;
    }
    .kept {
      font-style: italic;
    }
    .badge {
      white-space: nowrap;
      border-radius: 10px;
      padding: 1px 8px;
      border: 1px solid currentColor;
    }
    .badge.comfort {
      color: var(--success-color, var(--primary-color));
    }
    .badge.regulation {
      color: var(--warning-color, var(--primary-color));
    }
    .message {
      padding: 16px;
    }
    .message.error {
      color: var(--error-color);
    }
    .message.warning {
      color: var(--warning-color);
    }
    table.week th {
      width: 8em;
    }
    .scale {
      position: relative;
      height: 1.4em;
    }
    .scale span {
      position: absolute;
      transform: translateX(-50%);
      color: var(--secondary-text-color);
      font-size: 0.8em;
    }
    .day {
      position: relative;
      height: 14px;
      background: var(--secondary-background-color);
      border-radius: 4px;
    }
    .bar {
      position: absolute;
      top: 0;
      bottom: 0;
      background: var(--primary-color);
      border-radius: 4px;
    }
    .day-text {
      font-size: 0.85em;
      color: var(--secondary-text-color);
      margin-top: 2px;
    }
    dl {
      display: grid;
      grid-template-columns: minmax(0, max-content) minmax(0, 1fr);
      gap: 6px 16px;
    }
    dt {
      color: var(--secondary-text-color);
    }
    dd {
      margin: 0;
      min-width: 0; /* a long entity id wraps inside its column instead of widening the page */
      overflow-wrap: anywhere;
    }
    code {
      overflow-wrap: anywhere;
    }
    dd ul {
      margin: 0;
      padding-inline-start: 16px;
    }
    .error {
      color: var(--error-color);
    }
    button.primary {
      border: 0;
      border-radius: 6px;
      padding: 4px 12px;
      cursor: pointer;
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
    }
    button:disabled {
      opacity: 0.5;
      cursor: default;
    }
    form.edit {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 4px 8px;
      margin-top: 6px;
    }
    form.edit div {
      flex-basis: 100%;
    }
    input {
      font: inherit;
      padding: 4px 6px;
      color: var(--primary-text-color);
      background: var(--card-background-color);
      border: 1px solid var(--divider-color);
      border-radius: 6px;
    }
    input[type="number"] {
      width: 6em;
    }
    input[aria-invalid="true"] {
      border-color: var(--error-color);
    }
    .day.editable {
      cursor: crosshair;
      height: 22px;
      touch-action: none;
    }
    .day.editable .bar {
      cursor: pointer;
    }
    .day-edit {
      display: flex;
      flex-wrap: wrap;
      gap: 4px 12px;
      margin-top: 4px;
      align-items: center;
    }
    .day-edit input {
      flex: 1 1 14em;
      min-width: 0;
    }
    tr.changed th {
      font-weight: 500;
      color: var(--primary-color);
    }
    .actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      margin-top: 8px;
    }
    .backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.4);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 16px;
      z-index: 10;
    }
    .dialog {
      background: var(--card-background-color);
      color: var(--primary-text-color);
      border-radius: var(--ha-card-border-radius, 12px);
      padding: 16px 20px;
      max-width: 560px;
      width: 100%;
      max-height: 90vh;
      overflow: auto;
    }
    .visually-hidden {
      position: absolute;
      width: 1px;
      height: 1px;
      overflow: hidden;
      clip: rect(0 0 0 0);
      white-space: nowrap;
    }
    @media (max-width: 600px) {
      dl {
        grid-template-columns: 1fr;
      }
    }
  `;customElements.get("weishaupt-panel")||customElements.define("weishaupt-panel",B);function Xe(a){let[s,t]=a.split(":").map(Number);return s*60+(t||0)}export{B as WeishauptPanel};
/*! Bundled license information:

@lit/reactive-element/css-tag.js:
  (**
   * @license
   * Copyright 2019 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/reactive-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/lit-html.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-element/lit-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/is-server.js:
  (**
   * @license
   * Copyright 2022 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)
*/
